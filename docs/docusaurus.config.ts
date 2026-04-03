import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'IFRS 9 Expected Credit Losses',
  tagline: 'Enterprise ECL calculation platform on Databricks',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://databrickslabs.github.io',
  baseUrl: '/docs/',

  organizationName: 'databrickslabs',
  projectName: 'expected-credit-losses',

  onBrokenLinks: 'throw',

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
          sidebarId: 'docs',
          position: 'left',
          label: 'Documentation',
        },
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'User Guide',
          docsPluginId: 'default',
        },
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Admin Guide',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            { label: 'Getting Started', to: '/getting-started/installation' },
            { label: 'User Guide', to: '/user-guide/overview' },
            { label: 'Admin Guide', to: '/admin-guide/overview' },
          ],
        },
        {
          title: 'Reference',
          items: [
            { label: 'IFRS 9 Concepts', to: '/reference/ifrs9-concepts' },
            { label: 'API Reference', to: '/reference/api' },
            { label: 'Data Model', to: '/reference/data-model' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Databricks. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml', 'sql'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
