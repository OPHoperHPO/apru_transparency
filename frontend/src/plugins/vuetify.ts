import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'


const lightTheme = {
  dark: false,
  colors: {
    background: '#ffffff',
    surface: '#ffffff',
    'surface-variant': '#f8fafc',
    primary: '#6366f1',
    'primary-darken-1': '#4f46e5',
    secondary: '#64748b',
    'secondary-darken-1': '#475569',
    error: '#ef4444',
    info: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    'on-background': '#0f172a',
    'on-surface': '#1e293b',
    'on-surface-variant': '#64748b',
    'on-primary': '#ffffff',
    'on-secondary': '#ffffff',
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
    },
  },
  icons: {
    defaultSet: 'mdi',
    sets: {
      mdi,
    },
  },
  defaults: {
    VBtn: {
      style: 'text-transform: none; letter-spacing: normal;',
      variant: 'elevated',
      rounded: 'lg',
    },
    VCard: {
      rounded: 'xl',
      elevation: 0,
      style: 'border: 1px solid #e2e8f0;',
    },
    VTextField: {
      variant: 'outlined',
      rounded: 'lg',
    },
    VSelect: {
      variant: 'outlined', 
      rounded: 'lg',
    },
    VTextarea: {
      variant: 'outlined',
      rounded: 'lg',
    },
  },
})