import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'IFRS 9 ECL Platform',
  tagline: 'Expected Credit Loss calculation and reporting on Databricks',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://ecl-platform.databricks.com',
  baseUrl: '/docs/',
  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'IFRS 9 ECL',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'User Guide',
        },
        {
          to: '/admin-guide/setup-installation',
          position: 'left',
          label: 'Admin Guide',
        },
        {
          to: '/developer/architecture',
          position: 'left',
          label: 'Developer Reference',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Getting Started',
          items: [
            { label: 'What is IFRS 9 ECL?', to: '/overview' },
            { label: 'Your First ECL Project', to: '/quick-start' },
            { label: '8-Step Workflow', to: '/user-guide/workflow-overview' },
          ],
        },
        {
          title: 'User Guide',
          items: [
            { label: 'Model Registry', to: '/user-guide/model-registry' },
            { label: 'Backtesting', to: '/user-guide/backtesting' },
            { label: 'Regulatory Reports', to: '/user-guide/regulatory-reports' },
            { label: 'GL Journals', to: '/user-guide/gl-journals' },
            { label: 'FAQ', to: '/user-guide/faq' },
          ],
        },
        {
          title: 'Admin Guide',
          items: [
            { label: 'Setup & Installation', to: '/admin-guide/setup-installation' },
            { label: 'Data Mapping', to: '/admin-guide/data-mapping' },
            { label: 'Model Configuration', to: '/admin-guide/model-configuration' },
            { label: 'User Management', to: '/admin-guide/user-management' },
          ],
        },
        {
          title: 'Developer Reference',
          items: [
            { label: 'Architecture', to: '/developer/architecture' },
            { label: 'API Reference', to: '/developer/api-reference' },
            { label: 'Data Model', to: '/developer/data-model' },
            { label: 'ECL Engine', to: '/developer/ecl-engine' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} IFRS 9 ECL Platform. Built on Databricks.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'json'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
