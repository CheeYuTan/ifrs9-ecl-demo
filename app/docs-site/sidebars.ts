import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'overview',
    'getting-started',
    'architecture',
    {
      type: 'category',
      label: 'Feature Guides',
      items: [
        'guides/core-workflow-data',
        'guides/simulation-engine',
        'guides/model-analytics',
        'guides/operational-governance',
        'guides/ecl-engine',
        'guides/domain-logic-core',
        'guides/domain-logic-analytical',
        'guides/frontend-testing',
      ],
    },
    'faq',
  ],
};

export default sidebars;
