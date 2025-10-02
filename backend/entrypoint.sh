set -e
python - <<'PY'
import os, time, psycopg2
host=os.environ.get('POSTGRES_HOST','db')
port=int(os.environ.get('POSTGRES_PORT','5432'))
name=os.environ['POSTGRES_DB']; user=os.environ['POSTGRES_USER']; pw=os.environ['POSTGRES_PASSWORD']
for _ in range(60):
    try:
        psycopg2.connect(host=host,port=port,dbname=name,user=user,password=pw).close()
        break
    except Exception: time.sleep(1)
else:
    raise SystemExit('DB not ready')
PY
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput
if [ $? -eq 0 ]; then
    python manage.py bootstrap_worker_token || echo "Warning: bootstrap_worker_token failed"
    python manage.py seed_demo_users || echo "Warning: seed_demo_users failed"
fi
python manage.py runserver 0.0.0.0:8000
