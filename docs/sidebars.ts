import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'getting-started/installation',
        'getting-started/configuration',
        'getting-started/quick-start',
      ],
    },
    {
      type: 'category',
      label: 'User Guide',
      collapsed: false,
      items: [
        'user-guide/overview',
        {
          type: 'category',
          label: 'ECL Workflow (8 Steps)',
          collapsed: false,
          items: [
            'user-guide/create-project',
            'user-guide/data-processing',
            'user-guide/data-control',
            'user-guide/satellite-model',
            'user-guide/model-execution',
            'user-guide/stress-testing',
            'user-guide/overlays',
            'user-guide/sign-off',
          ],
        },
        'user-guide/model-registry',
        'user-guide/backtesting',
        'user-guide/gl-journals',
        'user-guide/regulatory-reports',
        'user-guide/approval-workflow',
      ],
    },
    {
      type: 'category',
      label: 'Admin Guide',
      collapsed: false,
      items: [
        'admin-guide/overview',
        'admin-guide/data-mapping',
        'admin-guide/model-config',
        'admin-guide/jobs-pipelines',
        'admin-guide/app-settings',
        'admin-guide/theme',
        {
          type: 'category',
          label: 'Theming (Technical)',
          collapsed: true,
          items: [
            'admin-guide/theming/light-dark-mode',
            'admin-guide/theming/core-components',
            'admin-guide/theming/workflow-pages',
            'admin-guide/theming/admin-secondary-pages',
            'admin-guide/theming/data-mapping-theming',
          ],
        },
        'admin-guide/system',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      collapsed: true,
      items: [
        'reference/ifrs9-concepts',
        'reference/api',
        'reference/data-model',
      ],
    },
  ],
};

export default sidebars;
