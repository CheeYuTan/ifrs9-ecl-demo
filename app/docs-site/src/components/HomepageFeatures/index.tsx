import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  icon: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: '3-Stage Impairment Model',
    icon: '📊',
    description: (
      <>
        Implements the full IFRS 9 three-stage impairment model with automated
        stage classification, SICR detection, and lifetime ECL calculation for
        Stage 2 and Stage 3 exposures.
      </>
    ),
  },
  {
    title: 'Monte Carlo Simulation',
    icon: '🎲',
    description: (
      <>
        Forward-looking ECL estimation using Monte Carlo simulation with
        Cholesky-correlated PD/LGD shocks, multiple macroeconomic scenarios,
        and probability-weighted outcomes.
      </>
    ),
  },
  {
    title: 'Regulatory Reporting',
    icon: '📋',
    description: (
      <>
        Generate IFRS 7 disclosure reports (paragraphs 35F–36), GL journal
        entries for ECL provisioning, and full audit trails with maker-checker
        governance and sign-off workflows.
      </>
    ),
  },
];

function Feature({title, icon, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center" style={{fontSize: '3rem', marginBottom: '0.5rem'}}>
        {icon}
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
