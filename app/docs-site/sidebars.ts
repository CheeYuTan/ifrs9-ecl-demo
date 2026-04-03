import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'overview',
        'quick-start',
      ],
    },
    {
      type: 'category',
      label: 'User Guide',
      collapsed: false,
      items: [
        'user-guide/workflow-overview',
        'user-guide/step-1-create-project',
        'user-guide/step-2-data-processing',
        'user-guide/step-3-data-control',
        'user-guide/step-4-satellite-model',
        'user-guide/step-5-model-execution',
        'user-guide/step-6-stress-testing',
        'user-guide/step-7-overlays',
        'user-guide/step-8-sign-off',
        'user-guide/model-registry',
        'user-guide/backtesting',
        'user-guide/regulatory-reports',
        'user-guide/gl-journals',
        'user-guide/approval-workflow',
        'user-guide/attribution',
        'user-guide/markov-hazard',
        'user-guide/advanced-features',
        'user-guide/faq',
      ],
    },
    {
      type: 'category',
      label: 'Admin Guide',
      items: [
        'admin-guide/setup-installation',
        'admin-guide/data-mapping',
        'admin-guide/model-configuration',
        'admin-guide/app-settings',
        'admin-guide/jobs-pipelines',
        'admin-guide/theme-customization',
        'admin-guide/system-administration',
        'admin-guide/user-management',
        'admin-guide/troubleshooting',
      ],
    },
    {
      type: 'category',
      label: 'Developer Reference',
      items: [
        'developer/architecture',
        'developer/api-reference',
        'developer/data-model',
        'developer/ecl-engine',
        'developer/testing',
      ],
    },
  ],
};

export default sidebars;
