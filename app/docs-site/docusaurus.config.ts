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
  baseUrl: '/',

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
          routeBasePath: 'docs',
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
          label: 'Documentation',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            { label: 'Overview', to: '/docs/overview' },
            { label: 'Getting Started', to: '/docs/getting-started' },
            { label: 'Architecture', to: '/docs/architecture' },
          ],
        },
        {
          title: 'Guides',
          items: [
            { label: 'Core Workflow & Data', to: '/docs/guides/core-workflow-data' },
            { label: 'Simulation Engine', to: '/docs/guides/simulation-engine' },
            { label: 'Model Analytics', to: '/docs/guides/model-analytics' },
            { label: 'Operations & Governance', to: '/docs/guides/operational-governance' },
            { label: 'ECL Engine', to: '/docs/guides/ecl-engine' },
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
