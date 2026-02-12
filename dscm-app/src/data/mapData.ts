// Types for the supply chain map
export interface Material {
  name: string;
  placeholder: string;
}

export interface Box {
  id: string;
  title: string;
  materials: Material[];
  borderColor: string;
  statusType: 'success' | 'warning' | 'danger';
  tooltipText?: string;
  hasKpi: boolean;
}

export interface Stage {
  id: string;
  name: string;
  labelColor: string;
  boxes: Box[];
}

export interface Connection {
  from: string;
  to: string;
  color: string;
}

// Stage data
export const stages: Stage[] = [
  {
    id: 'rsm',
    name: 'RSM',
    labelColor: '#6b7280',
    boxes: [
      {
        id: 'rsm-1',
        title: 'RSM Box 1',
        borderColor: '#eab308',
        statusType: 'success',
        hasKpi: false,
        materials: [
          { name: 'Material A', placeholder: '(placeholder)' },
          { name: 'Material B', placeholder: '(placeholder)' },
          { name: 'Material C', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'rsm-2',
        title: 'RSM Box 2',
        borderColor: '#ef4444',
        statusType: 'success',
        hasKpi: false,
        materials: [
          { name: 'Material D', placeholder: '(placeholder)' },
          { name: 'Material E', placeholder: '(placeholder)' },
          { name: 'Material F', placeholder: '(placeholder)' },
          { name: 'Material G', placeholder: '(placeholder)' },
          { name: 'Material H', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'rsm-3',
        title: 'RSM Box 3',
        borderColor: '#eab308',
        statusType: 'success',
        hasKpi: false,
        materials: [
          { name: 'Material I', placeholder: '(placeholder)' },
        ],
      },
    ],
  },
  {
    id: 'intermediate',
    name: 'Intermediate',
    labelColor: '#3b82f6',
    boxes: [
      {
        id: 'intermediate-1',
        title: 'Intermediate Box 1',
        borderColor: '#eab308',
        statusType: 'success',
        hasKpi: false,
        materials: [
          { name: 'Intermediate A', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'intermediate-2',
        title: 'Intermediate Box 2',
        borderColor: '#eab308',
        statusType: 'success',
        hasKpi: false,
        materials: [
          { name: 'Intermediate B', placeholder: '(placeholder)' },
        ],
      },
    ],
  },
  {
    id: 'api',
    name: 'API',
    labelColor: '#22c55e',
    boxes: [
      {
        id: 'api-1',
        title: 'API Box 1',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'API Component A', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'api-2',
        title: 'API Box 2',
        borderColor: '#eab308',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'API Component B', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'api-3',
        title: 'API Box 3',
        borderColor: '#eab308',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'API Component C', placeholder: '(placeholder)' },
        ],
      },
    ],
  },
  {
    id: 'formulation',
    name: 'Formulation',
    labelColor: '#8b5cf6',
    boxes: [
      {
        id: 'formulation-1',
        title: 'Formulation Box 1',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Formulation A', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'formulation-2',
        title: 'Formulation Box 2',
        borderColor: '#3b82f6',
        statusType: 'danger',
        hasKpi: true,
        tooltipText: "Impact: This Plant B's production of Material X is at risk due to delay of inventory from Plant A (API) to Plant B (Formulation).",
        materials: [
          { name: 'Formulation B', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'formulation-3',
        title: 'Formulation Box 3',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Formulation C', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'formulation-4',
        title: 'Formulation Box 4',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Formulation D', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'formulation-5',
        title: 'Formulation Box 5',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Formulation E', placeholder: '(placeholder)' },
        ],
      },
    ],
  },
  {
    id: 'packaging',
    name: 'Packaging',
    labelColor: '#1e40af',
    boxes: [
      {
        id: 'packaging-1',
        title: 'Packaging Box 1',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Packaging Line A', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'packaging-2',
        title: 'Packaging Box 2',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Packaging Line B', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'packaging-3',
        title: 'Packaging Box 3',
        borderColor: '#3b82f6',
        statusType: 'warning',
        hasKpi: true,
        tooltipText: "Impact: This Plant C's packaging of Material X is at potential risk due to delay of inventory from Formulation Plant B to Packaging Plant C.",
        materials: [
          { name: 'Packaging Line C', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'packaging-4',
        title: 'Packaging Box 4',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Packaging Line D', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'packaging-5',
        title: 'Packaging Box 5',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Packaging Line E', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'packaging-6',
        title: 'Packaging Box 6',
        borderColor: '#3b82f6',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Packaging Line F', placeholder: '(placeholder)' },
        ],
      },
    ],
  },
  {
    id: 'customer-market',
    name: 'Customer Market',
    labelColor: '#eab308',
    boxes: [
      {
        id: 'customer-1',
        title: 'Customer Box 1',
        borderColor: '#6b7280',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Market A', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'customer-2',
        title: 'Customer Box 2',
        borderColor: '#6b7280',
        statusType: 'warning',
        hasKpi: true,
        tooltipText: "Impact: This market sales of Brand Y is at potential risk due to delay of inventory from Packaging Plant C to Market.",
        materials: [
          { name: 'Market B', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'customer-3',
        title: 'Customer Box 3',
        borderColor: '#6b7280',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Market C', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'customer-4',
        title: 'Customer Box 4',
        borderColor: '#6b7280',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Market D', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'customer-5',
        title: 'Customer Box 5',
        borderColor: '#6b7280',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Market E', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'customer-6',
        title: 'Customer Box 6',
        borderColor: '#6b7280',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Market F', placeholder: '(placeholder)' },
        ],
      },
      {
        id: 'customer-7',
        title: 'Customer Box 7',
        borderColor: '#6b7280',
        statusType: 'success',
        hasKpi: true,
        materials: [
          { name: 'Market G', placeholder: '(placeholder)' },
        ],
      },
    ],
  },
];

// Connection data
export const connections: Connection[] = [
  // RSM to Intermediate
  { from: 'rsm-1', to: 'intermediate-1', color: '#000000' },
  { from: 'rsm-2', to: 'intermediate-1', color: '#000000' },
  { from: 'rsm-3', to: 'intermediate-2', color: '#000000' },

  // Intermediate to API
  { from: 'intermediate-1', to: 'api-2', color: '#000000' },
  { from: 'intermediate-2', to: 'api-3', color: '#000000' },

  // API internal
  { from: 'api-2', to: 'api-1', color: '#000000' },

  // API to Formulation
  { from: 'api-1', to: 'formulation-1', color: '#000000' },
  { from: 'api-1', to: 'formulation-3', color: '#000000' },
  { from: 'api-1', to: 'formulation-4', color: '#000000' },
  { from: 'api-2', to: 'formulation-2', color: '#000000' },
  { from: 'api-2', to: 'formulation-5', color: '#000000' },
  { from: 'api-3', to: 'formulation-2', color: '#ef4444' }, // Red - high risk

  // Formulation to Packaging
  { from: 'formulation-1', to: 'packaging-1', color: '#000000' },
  { from: 'formulation-1', to: 'packaging-2', color: '#000000' },
  { from: 'formulation-1', to: 'packaging-3', color: '#000000' },
  { from: 'formulation-1', to: 'packaging-4', color: '#000000' },
  { from: 'formulation-2', to: 'packaging-2', color: '#000000' },
  { from: 'formulation-2', to: 'packaging-3', color: '#f59e0b' }, // Amber - potential risk
  { from: 'formulation-3', to: 'packaging-5', color: '#000000' },
  { from: 'formulation-4', to: 'packaging-6', color: '#000000' },

  // Formulation to Customer (direct)
  { from: 'formulation-3', to: 'customer-6', color: '#000000' },

  // Packaging to Customer
  { from: 'packaging-1', to: 'customer-4', color: '#000000' },
  { from: 'packaging-1', to: 'customer-5', color: '#000000' },
  { from: 'packaging-2', to: 'customer-3', color: '#000000' },
  { from: 'packaging-3', to: 'customer-2', color: '#f59e0b' }, // Amber - potential risk
  { from: 'packaging-4', to: 'customer-1', color: '#000000' },
  { from: 'packaging-5', to: 'customer-5', color: '#000000' },
  { from: 'packaging-6', to: 'customer-7', color: '#000000' },
];

// Chat assist data
export const chatSummary = [
  "Delay from API Plant A to Formulation Plant B is impacting Material X.",
  "Formulation Plant B is at risk (red).",
  "Packaging Plant C and Market Box2 are at potential risk (amber).",
];

export const suggestedQuestions = [
  {
    id: 'q1',
    question: "Why is Formulation Plant B at risk?",
    answer: "Formulation Plant B depends on inbound API inventory from Plant A. The detected delay reduces inventory coverage below the safety threshold for Material X, putting production at risk. Note: Answer is generated from Knowledge Graph"
  },
  {
    id: 'q2',
    question: "Which downstream sites/markets are impacted and how severe?",
    answer: "High risk: Formulation Box2 (production disruption likely).\nPotential risk: Packaging Box3 (may miss packaging schedule), Customer Market Box2 (sales/service risk).\nOther connected paths remain stable based on current coverage placeholders. Note: Answer is generated from Knowledge Graph"
  },
  {
    id: 'q3',
    question: "What are the recommended actions to reduce risk?",
    answer: "Recommended actions (Recommendation is generated from Aera):\n• Expedite API shipment from Plant A (priority lane).\n• Rebalance allocation to protect Market Box2 demand.\n• Pull forward packaging at Plant C for available lots.\n• Evaluate alternate sourcing/site if delay exceeds threshold."
  },
];

// Organization key legend
export const organizationLegend = [
  { label: 'AZ Site', color: '#3b82f6' },
  { label: 'External ESM Site', color: '#eab308' },
  { label: '3PS', color: '#166534' },
  { label: 'External NON ESM Site', color: '#ef4444' },
];

// Team legend
export const teamLegend = ['GBP', 'GSSD', 'GST QL'];

// Brands
export const brands = ['Brand A', 'Brand B', 'Brand C'];
