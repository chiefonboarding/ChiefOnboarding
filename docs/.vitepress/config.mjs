import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "ChiefOnboarding",
  description: "Self-hosted employee onboarding platform",
  lastUpdated: true,
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    logo: 'static/logo.png',
    siteTitle: false,
    search: {
      provider: 'local'
    },
    editLink: {
      pattern: 'https://github.com/chiefonboarding/chiefonboarding/edit/master/docs/:path'
    },
    nav: [
      { text: 'Home', link: '/' },
      { text: "What's ChiefOnboarding", link: '/whatschiefonboarding' }
    ],

    sidebar: [
      {
        text: "What's ChiefOnboarding",
        link: 'whatschiefonboarding'
      },
      {
        text: 'Demo / How to',
        link: 'howto'
      },
      {
        text: 'Deployment',
        collapsed: false,
        items: [
          { text: 'Docker', link: 'deployment/docker' },
          { text: 'Heroku', link: 'deployment/heroku' },
          { text: 'Render', link: 'deployment/render' }
        ]
      },
      {
        text: 'Configuration',
        collapsed: false,
        items: [
          { text: 'Object storage (up/downloading files)', link: 'config/objectstorage' },
          { text: 'Email', link: 'config/email' },
          { text: 'Ratelimits', link: 'config/ratelimits' },
          { text: 'Text messages', link: 'config/textmessages' },
          { text: 'Error logging', link: 'config/errorlogging' },
          { text: 'Google SSO', link: 'config/google-sso' },
          { text: 'Slackbot', link: 'config/slackbot' },
          { text: 'OIDC Single Sign-On (SSO)', link: 'config/oidc' },
        ]
      },
      {
        text: 'Development',
        link: 'development'
      },
      {
        text: 'API',
        link: 'api'
      },
      {
        text: 'Custom integrations',
        collapsed: false,
        items: [
          { text: 'Introduction', link: 'integrations/intro' },
          { 
              text: 'Webhooks/Account provisioning', 
              link: 'integrations/webhooks',
              collapsed: false,
              items: [
                { text: 'Form', link: 'integrations/form' },
                { text: 'Headers', link: 'integrations/headers' },
                { text: 'Exists', link: 'integrations/exists' },
                { text: 'Revoke', link: 'integrations/revoke' },
                { text: 'Execute', link: 'integrations/execute' },
                { text: 'Initial data form', link: 'integrations/initial-data-form' },
                { text: 'Post execute notification', link: 'integrations/post-execution-notification' },
                { text: 'Oauth', link: 'integrations/oauth' },
              ]
          },
          { 
              text: 'Create or sync users', 
              link: 'integrations/sync',
              collapsed: false,
              items: [
                { text: 'Headers', link: 'integrations/headers' },
                { text: 'Execute', link: 'integrations/execute' },
                { text: 'Initial data form', link: 'integrations/initial-data-form' },
                { text: 'Action', link: 'integrations/action' },
                { text: 'Data from', link: 'integrations/data-from' },
                { text: 'Data structure', link: 'integrations/data-structure' },
                { text: 'Schedule', link: 'integrations/schedule' },
                { text: 'Paginated response', link: 'integrations/paginated-response' },
              ]
          }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/chiefonboarding/chiefonboarding' }
    ]
  }
})
