from app.celery import app
from django.utils import timezone
from django.db import transaction
from .models import Task
@app.task
def touch_queue(task_id: str):
    return {"task_id": task_id}
@app.task
def requeue_stale_tasks():
    now = timezone.now()
    stale = Task.objects.filter(status=Task.Status.IN_PROGRESS)
    for t in stale:
        pivot = t.heartbeat_at or t.started_at or t.updated_at
        if not pivot:
            continue
        age = (now - pivot).total_seconds()
        if age > (t.ttl_seconds or 3600):
            with transaction.atomic():
                _t = Task.objects.select_for_update().get(id=t.id)
                if _t.status != Task.Status.IN_PROGRESS:
                    continue
                if _t.retry_count < (_t.max_retries or 0):
                    _t.status = Task.Status.QUEUED
                    _t.assigned_to = None
                    _t.started_at = None
                    _t.heartbeat_at = None
                    _t.retry_count = (_t.retry_count or 0) + 1
                    if not _t.error:
                        _t.error = "requeued after TTL"
                    _t.save(update_fields=["status","assigned_to","started_at","heartbeat_at","retry_count","error","updated_at"])
                else:
                    _t.status = Task.Status.FAILED
                    _t.finished_at = now
                    if not _t.error:
                        _t.error = "failed after TTL; retries exhausted"
                    _t.save(update_fields=["status","finished_at","error","updated_at"])
    return {"ok": True}
@app.task
def analyze_document_with_legal_llm(task_id: str, file_content: bytes, filename: str):
    from app.agents.legal_llm import analyze_contract
    from app.agents.document_extractor import extract_text_from_file
    from app.projects.models import Project
    try:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.IN_PROGRESS
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at', 'updated_at'])
        try:
            document_text = extract_text_from_file(file_content, filename)
        except ValueError as e:
            task.status = Task.Status.FAILED
            task.error = f"Text extraction failed: {str(e)}"
            task.finished_at = timezone.now()
            task.save(update_fields=['status', 'error', 'finished_at', 'updated_at'])
            raise
        result = analyze_contract(document_text, contract_id=task_id)
        result_dict = {
            'contract_id': result.contract_id,
            'analysis_date': result.analysis_date,
            'overall_compliance_score': result.overall_compliance_score,
            'summary': result.summary,
            'critical_issues': result.critical_issues,
            'recommendations': result.recommendations,
            'criteria': {},
            'document_info': {
                'filename': filename,
                'text_length': len(document_text),
                'extraction_method': 'auto'
            }
        }
        for field_name in result.__annotations__:
            if field_name not in ['contract_id', 'analysis_date', 'overall_compliance_score',
                                   'summary', 'critical_issues', 'recommendations']:
                criterion = getattr(result, field_name)
                if hasattr(criterion, 'status'):
                    result_dict['criteria'][field_name] = {
                        'status': criterion.status,
                        'explanation': criterion.explanation,
                        'recommendations': criterion.recommendations,
                        'confidence_score': criterion.confidence_score
                    }
        task.result_json = result_dict
        task.status = Task.Status.DONE
        task.finished_at = timezone.now()
        task.save(update_fields=['result_json', 'status', 'finished_at', 'updated_at'])
        if task.project:
            trust_score = result.overall_compliance_score * 100
            task.project.trust_score = trust_score
            task.project.status = Project.Status.UNDER_REVIEW
            task.project.save(update_fields=['trust_score', 'status', 'updated_at'])
        return {'task_id': task_id, 'status': 'success'}
    except Exception as e:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.FAILED
        task.error = str(e)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error', 'finished_at', 'updated_at'])
        raise
@app.task
def analyze_website_with_browser_agent(task_id: str, url: str):
    from app.projects.models import Project
    from app.agents.dynamic_agent import analyze_website
    try:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.IN_PROGRESS
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at', 'updated_at'])
        result_dict = analyze_website(url)
        task.result_json = result_dict
        task.status = Task.Status.DONE
        task.finished_at = timezone.now()
        task.save(update_fields=['result_json', 'status', 'finished_at', 'updated_at'])
        if task.project:
            task.project.trust_score = result_dict.get('transparency_score', 75.0)
            task.project.status = Project.Status.UNDER_REVIEW
            task.project.save(update_fields=['trust_score', 'status', 'updated_at'])
        return {'task_id': task_id, 'status': 'success'}
    except Exception as e:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.FAILED
        task.error = str(e)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error', 'finished_at', 'updated_at'])
        raise
@app.task
def detect_roach_motel_pattern(task_id: str, url: str, test_service: str = None):
    from app.projects.models import Project
    import os
    try:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.IN_PROGRESS
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at', 'updated_at'])
        from app.agents.dynamic_agent.agents.roach_motel_agent import roach_motel_root_agent
        initial_state = {
            "request": f"Test {url} for Roach Motel pattern" + (f" - {test_service}" if test_service else ""),
            "target_site": url,
            "test_service": test_service
        }
        result = roach_motel_root_agent.run(state=initial_state)
        metrics = result.get("metrics_to_collect", {})
        result_dict = {
            'pattern_type': 'roach_motel',
            'url': url,
            'detected': bool(metrics.get('sar_ratio', 0) > 2.0),
            'severity': 'high' if metrics.get('sar_ratio', 0) > 3.0 else 'medium' if metrics.get('sar_ratio', 0) > 2.0 else 'low',
            'metrics': metrics,
            'summary': result.get('final_summary', 'Pattern detection completed'),
            'details': result.get('final_data', {})
        }
        task.result_json = result_dict
        task.status = Task.Status.DONE
        task.finished_at = timezone.now()
        task.save(update_fields=['result_json', 'status', 'finished_at', 'updated_at'])
        return {'task_id': task_id, 'status': 'success'}
    except Exception as e:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.FAILED
        task.error = str(e)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error', 'finished_at', 'updated_at'])
        raise
@app.task
def detect_fake_urgency_pattern(task_id: str, url: str):
    from app.projects.models import Project
    try:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.IN_PROGRESS
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at', 'updated_at'])
        from app.agents.dynamic_agent.agents.fake_urgency_agent import fake_urgency_root_agent
        initial_state = {
            "request": f"Test {url} for Fake Urgency pattern",
            "target_site": url
        }
        result = fake_urgency_root_agent.run(state=initial_state)
        metrics = result.get("metrics", {})
        result_dict = {
            'pattern_type': 'fake_urgency',
            'url': url,
            'detected': bool(metrics.get('timer_resets', 0) > 0 or metrics.get('false_countdown', False)),
            'severity': 'high' if metrics.get('timer_resets', 0) > 2 else 'medium',
            'metrics': metrics,
            'summary': result.get('final_summary', 'Pattern detection completed'),
            'details': result.get('final_data', {})
        }
        task.result_json = result_dict
        task.status = Task.Status.DONE
        task.finished_at = timezone.now()
        task.save(update_fields=['result_json', 'status', 'finished_at', 'updated_at'])
        return {'task_id': task_id, 'status': 'success'}
    except Exception as e:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.FAILED
        task.error = str(e)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error', 'finished_at', 'updated_at'])
        raise
@app.task
def detect_drip_pricing_pattern(task_id: str, url: str):
    from app.projects.models import Project
    try:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.IN_PROGRESS
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at', 'updated_at'])
        from app.agents.dynamic_agent.agents.drip_pricing_agent import drip_pricing_root_agent
        initial_state = {
            "request": f"Test {url} for Drip Pricing pattern",
            "target_site": url
        }
        result = drip_pricing_root_agent.run(state=initial_state)
        metrics = result.get("metrics", {})
        price_increase = metrics.get('final_price', 0) - metrics.get('initial_price', 0)
        result_dict = {
            'pattern_type': 'drip_pricing',
            'url': url,
            'detected': bool(price_increase > 0 and metrics.get('hidden_fees_count', 0) > 0),
            'severity': 'high' if price_increase > metrics.get('initial_price', 1) * 0.3 else 'medium',
            'metrics': metrics,
            'summary': result.get('final_summary', 'Pattern detection completed'),
            'details': result.get('final_data', {})
        }
        task.result_json = result_dict
        task.status = Task.Status.DONE
        task.finished_at = timezone.now()
        task.save(update_fields=['result_json', 'status', 'finished_at', 'updated_at'])
        return {'task_id': task_id, 'status': 'success'}
    except Exception as e:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.FAILED
        task.error = str(e)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error', 'finished_at', 'updated_at'])
        raise
@app.task
def detect_all_dark_patterns(task_id: str, url: str):
    from app.projects.models import Project
    try:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.IN_PROGRESS
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at', 'updated_at'])
        all_results = {
            'url': url,
            'scan_date': timezone.now().isoformat(),
            'patterns_detected': [],
            'pattern_results': {}
        }
        pattern_tasks = [
            ('roach_motel', 'app.agents.dynamic_agent.agents.roach_motel_agent', 'roach_motel_root_agent'),
            ('fake_urgency', 'app.agents.dynamic_agent.agents.fake_urgency_agent', 'fake_urgency_root_agent'),
            ('fake_scarcity', 'app.agents.dynamic_agent.agents.fake_scarcity_agent', 'fake_scarcity_root_agent'),
            ('drip_pricing', 'app.agents.dynamic_agent.agents.drip_pricing_agent', 'drip_pricing_root_agent'),
            ('hidden_subscription', 'app.agents.dynamic_agent.agents.hidden_subscription_agent', 'hidden_subscription_root_agent'),
            ('sneak_into_basket', 'app.agents.dynamic_agent.agents.sneak_into_basket_agent', 'sneak_into_basket_root_agent'),
            ('bait_and_switch', 'app.agents.dynamic_agent.agents.bait_and_switch_agent', 'bait_and_switch_root_agent'),
            ('confirmshaming', 'app.agents.dynamic_agent.agents.confirmshaming_agent', 'confirmshaming_root_agent'),
            ('forced_actions', 'app.agents.dynamic_agent.agents.forced_actions_agent', 'forced_actions_root_agent'),
            ('nagging', 'app.agents.dynamic_agent.agents.nagging_agent', 'nagging_root_agent'),
            ('navigation_obstacles', 'app.agents.dynamic_agent.agents.navigation_obstacles_agent', 'navigation_obstacles_root_agent'),
            ('currency_manipulation', 'app.agents.dynamic_agent.agents.currency_manipulation_agent', 'currency_manipulation_root_agent'),
        ]
        for pattern_name, module_path, agent_name in pattern_tasks:
            try:
                module = __import__(module_path, fromlist=[agent_name])
                agent = getattr(module, agent_name)
                initial_state = {
                    "request": f"Test {url} for {pattern_name.replace('_', ' ').title()} pattern",
                    "target_site": url
                }
                result = agent.run(state=initial_state)
                pattern_result = {
                    'detected': bool(result.get('final_data', {}).get('detected', False)),
                    'severity': result.get('final_data', {}).get('severity', 'unknown'),
                    'metrics': result.get('final_data', {}),
                    'summary': result.get('final_summary', '')
                }
                all_results['pattern_results'][pattern_name] = pattern_result
                if pattern_result['detected']:
                    all_results['patterns_detected'].append(pattern_name)
            except Exception as pattern_error:
                all_results['pattern_results'][pattern_name] = {
                    'error': str(pattern_error),
                    'detected': False
                }
        detected_count = len(all_results['patterns_detected'])
        total_patterns = len(pattern_tasks)
        transparency_score = max(0, min(100, 100 - (detected_count / total_patterns * 100)))
        all_results['transparency_score'] = transparency_score
        all_results['total_patterns_tested'] = total_patterns
        all_results['patterns_detected_count'] = detected_count
        task.result_json = all_results
        task.status = Task.Status.DONE
        task.finished_at = timezone.now()
        task.save(update_fields=['result_json', 'status', 'finished_at', 'updated_at'])
        if task.project:
            task.project.trust_score = transparency_score
            task.project.status = Project.Status.UNDER_REVIEW
            task.project.save(update_fields=['trust_score', 'status', 'updated_at'])
        return {'task_id': task_id, 'status': 'success', 'patterns_detected': detected_count}
    except Exception as e:
        task = Task.objects.get(id=task_id)
        task.status = Task.Status.FAILED
        task.error = str(e)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error', 'finished_at', 'updated_at'])
        raise
