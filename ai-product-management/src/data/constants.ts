export const MILESTONES = [
  {
    id: 'capture',
    phase: 1,
    title: 'Capture Opportunity',
    description: 'Document the initial idea, problem space, and strategic context.',
    status: 'completed' as const,
    tasks: [
      { title: 'Upload idea note or brief', completed: true },
      { title: 'Identify problem statement', completed: true },
      { title: 'Link to strategic priorities', completed: true },
    ],
    aiHint: 'AI can help structure raw ideas into a clear opportunity statement.',
    icon: 'Lightbulb',
    color: '#C4972F',
  },
  {
    id: 'shape',
    phase: 2,
    title: 'Shape Problem Statement',
    description: 'Refine the problem, validate assumptions, and define scope.',
    status: 'completed' as const,
    tasks: [
      { title: 'Draft problem hypothesis', completed: true },
      { title: 'Identify key assumptions', completed: true },
      { title: 'Define initial scope boundaries', completed: false },
    ],
    aiHint: 'AI can challenge assumptions and suggest alternative framings.',
    icon: 'Target',
    color: '#8B1A3A',
  },
  {
    id: 'value',
    phase: 3,
    title: 'Define Value & Outcomes',
    description: 'Articulate expected outcomes, success criteria, and user impact.',
    status: 'active' as const,
    tasks: [
      { title: 'Define success metrics', completed: true },
      { title: 'Map user outcomes', completed: false },
      { title: 'Draft value proposition', completed: false },
    ],
    aiHint: 'AI can generate outcome frameworks and benchmark against similar initiatives.',
    icon: 'TrendingUp',
    color: '#6C3483',
  },
  {
    id: 'brief',
    phase: 4,
    title: 'Create Product Brief',
    description: 'Compile a structured brief ready for review and alignment.',
    status: 'upcoming' as const,
    tasks: [
      { title: 'Generate brief from template', completed: false },
      { title: 'Add user stories and requirements', completed: false },
      { title: 'Attach supporting evidence', completed: false },
    ],
    aiHint: 'AI can draft a PRD from your inputs and flag gaps.',
    icon: 'FileText',
    color: '#2E86C1',
  },
  {
    id: 'prioritize',
    phase: 5,
    title: 'Prioritise & Align',
    description: 'Score, rank, and align with stakeholders on priorities.',
    status: 'upcoming' as const,
    tasks: [
      { title: 'Run prioritization framework', completed: false },
      { title: 'Identify stakeholders', completed: false },
      { title: 'Schedule alignment review', completed: false },
    ],
    aiHint: 'AI can apply RICE/MoSCoW scoring and draft stakeholder comms.',
    icon: 'BarChart3',
    color: '#148F77',
  },
  {
    id: 'plan',
    phase: 6,
    title: 'Plan Delivery',
    description: 'Build a delivery plan with milestones, risks, and dependencies.',
    status: 'upcoming' as const,
    tasks: [
      { title: 'Draft delivery milestones', completed: false },
      { title: 'Surface risks and dependencies', completed: false },
      { title: 'Build first project plan', completed: false },
    ],
    aiHint: 'AI can generate a project plan and identify common risk patterns.',
    icon: 'Calendar',
    color: '#C4972F',
  },
  {
    id: 'launch',
    phase: 7,
    title: 'Launch Readiness',
    description: 'Prepare for launch with final checks, comms, and go/no-go criteria.',
    status: 'upcoming' as const,
    tasks: [
      { title: 'Complete readiness checklist', completed: false },
      { title: 'Draft launch communications', completed: false },
      { title: 'Confirm go/no-go criteria', completed: false },
    ],
    aiHint: 'AI can generate launch checklists and draft release communications.',
    icon: 'Rocket',
    color: '#8B1A3A',
  },
];

export const PROJECTS = [
  {
    id: '1',
    name: 'SOP Assistant',
    description: 'An AI-powered tool to help teams create, review, and maintain Standard Operating Procedures across clinical and operational functions.',
    status: 'in_progress' as const,
    progress: 50,
    completedTasks: 2,
    totalTasks: 4,
    currentMilestone: 'Define Value & Outcomes',
    lastUpdated: '2 hours ago',
    color: '#8B1A3A',
  },
  {
    id: '2',
    name: 'Clinical Trial Dashboard',
    description: 'A unified dashboard for monitoring clinical trial progress, patient enrollment, and site performance across therapeutic areas.',
    status: 'in_progress' as const,
    progress: 72,
    completedTasks: 5,
    totalTasks: 7,
    currentMilestone: 'Create Product Brief',
    lastUpdated: '1 day ago',
    color: '#6C3483',
  },
  {
    id: '3',
    name: 'Supply Chain Predictor',
    description: 'Predictive analytics for pharmaceutical supply chain disruption and demand forecasting.',
    status: 'planning' as const,
    progress: 15,
    completedTasks: 1,
    totalTasks: 6,
    currentMilestone: 'Capture Opportunity',
    lastUpdated: '3 days ago',
    color: '#148F77',
  },
];

// ─── Per-Project Milestones ─────────────────────────────────────
// Each project has its own copy of milestones at different stages

function makeMilestones(completedPhases: number, activeTasksCompleted: number = 0): typeof MILESTONES {
  return MILESTONES.map((m, i) => ({
    ...m,
    status: i < completedPhases
      ? 'completed' as const
      : i === completedPhases
        ? 'active' as const
        : 'upcoming' as const,
    tasks: m.tasks.map((t, ti) => ({
      ...t,
      completed: i < completedPhases
        ? true
        : i === completedPhases && ti < activeTasksCompleted
          ? true
          : false,
    })),
  }));
}

export const PROJECT_MILESTONES: Record<string, typeof MILESTONES> = {
  // SOP Assistant — in Phase 3 (Define Value & Outcomes), 1 of 3 tasks done
  '1': makeMilestones(2, 1),
  // Clinical Trial Dashboard — in Phase 4 (Create Product Brief), 2 of 3 tasks done
  '2': makeMilestones(3, 2),
  // Supply Chain Predictor — in Phase 1 (Capture Opportunity), 1 of 3 tasks done
  '3': makeMilestones(0, 1),
};

export const GUIDANCE_ITEMS = [
  {
    id: '1',
    category: 'PM Task',
    title: 'User Requirements Specification',
    description: 'A URS formally documents what users need from a system before development begins. It captures functional requirements, constraints, user profiles, and measurable success criteria.',
    icon: 'FileText',
    color: '#8B1A3A',
    steps: [
      { title: 'Collect your raw inputs', description: 'Gather meeting transcripts, email threads, and existing documentation.' },
      { title: 'Extract requirements with AI', description: 'Paste transcripts and prompt AI to extract functional and non-functional requirements as user stories.' },
      { title: 'Apply the AZ URS template', description: 'Feed extracted requirements into the standard AstraZeneca URS template.' },
      { title: 'Run a gap analysis', description: 'Prompt AI to review for gaps, contradictions, ambiguous language, or missing edge cases.' },
    ],
    examplePrompt: 'Here are my stakeholder interview transcripts. Please extract functional requirements, group them by feature area, and format each as a user story with a clear acceptance criterion. Flag any that are ambiguous or contradictory.',
  },
  {
    id: '2',
    category: 'PM Task',
    title: 'Risk Assessment',
    description: 'A Risk Assessment identifies potential threats to project success, evaluates their likelihood and impact, and defines mitigation strategies.',
    icon: 'AlertTriangle',
    color: '#C4972F',
    steps: [
      { title: 'List known risks', description: 'Capture all risks from stakeholder interviews, project context, and domain knowledge.' },
      { title: 'Categorise and score', description: 'Use AI to apply likelihood × impact scoring and categorise risks by type.' },
      { title: 'Generate mitigations', description: 'Prompt AI to suggest mitigation strategies for each high-priority risk.' },
      { title: 'Build the risk register', description: 'Compile into a structured risk register with owners and review dates.' },
    ],
    examplePrompt: 'Review this project brief and identify the top 10 risks. For each, provide: risk description, category, likelihood (1-5), impact (1-5), and a suggested mitigation strategy.',
  },
  {
    id: '3',
    category: 'PM Task',
    title: 'Stakeholder Interview',
    description: 'Stakeholder interviews are structured conversations to understand user needs, pain points, expectations, and constraints from those affected by or accountable for an initiative.',
    icon: 'Users',
    color: '#6C3483',
    steps: [
      { title: 'Generate interview questions with AI', description: 'Prompt AI to create 15 structured questions covering current processes, pain points, desired outcomes, and success criteria.' },
      { title: 'Record and transcribe', description: 'Use Microsoft Teams auto-transcript or Otter.ai. Save to your SharePoint project folder.' },
      { title: 'AI summarisation', description: 'Extract key themes, stated needs, concerns, success criteria, and open questions.' },
      { title: 'Extract action items', description: 'Identify all action items, commitments, and follow-up questions from the transcript.' },
    ],
    examplePrompt: 'Here is a Teams meeting transcript. Please extract: (1) stakeholder key needs, (2) pain points mentioned, (3) constraints or blockers, (4) any requirements stated, and (5) action items and owners. Format as a structured interview summary with clear sections.',
  },
  {
    id: '4',
    category: 'PM Task',
    title: 'Vision for a New Initiative',
    description: 'A Vision statement describes the desired future state — what success looks like, who it benefits, and why it matters strategically.',
    icon: 'Compass',
    color: '#2E86C1',
    steps: [
      { title: 'Define the problem space', description: 'Articulate the current pain points and unmet needs clearly.' },
      { title: 'Draft the vision with AI', description: 'Prompt AI to generate a vision statement aligned with AZ strategic priorities.' },
      { title: 'Test with stakeholders', description: 'Share the draft vision for feedback and iterate.' },
      { title: 'Finalise and socialise', description: 'Lock the vision and embed it into project documentation.' },
    ],
    examplePrompt: 'Based on this problem statement and stakeholder feedback, draft a compelling vision statement for this initiative. It should be 2-3 sentences, aspirational but achievable, and clearly articulate who benefits and how.',
  },
  {
    id: '5',
    category: 'Template',
    title: 'Product Brief Template',
    description: 'A structured template for creating comprehensive product briefs that capture context, requirements, success criteria, and delivery approach.',
    icon: 'Layout',
    color: '#148F77',
    steps: [
      { title: 'Start from template', description: 'Use the AZ product brief template as your starting point.' },
      { title: 'Auto-populate with AI', description: 'Feed your research inputs and let AI draft initial sections.' },
      { title: 'Review and refine', description: 'Iterate on each section with stakeholder input.' },
      { title: 'Share for approval', description: 'Distribute for sign-off via standard governance channels.' },
    ],
    examplePrompt: 'Using the following inputs (problem statement, stakeholder feedback, and success criteria), draft a complete product brief following the AstraZeneca standard template format.',
  },
  {
    id: '6',
    category: 'Method',
    title: 'RICE Prioritisation',
    description: 'A quantitative framework for scoring and ranking initiatives based on Reach, Impact, Confidence, and Effort.',
    icon: 'Calculator',
    color: '#C4972F',
    steps: [
      { title: 'List initiatives', description: 'Compile all candidate features or initiatives to be prioritised.' },
      { title: 'Score with AI assistance', description: 'Use AI to help estimate Reach, Impact, Confidence, and Effort for each.' },
      { title: 'Rank and discuss', description: 'Review the ranked list with stakeholders and adjust where needed.' },
      { title: 'Document decisions', description: 'Record the final prioritisation and rationale.' },
    ],
    examplePrompt: 'Here are 8 feature proposals for our platform. Please score each using the RICE framework (Reach, Impact, Confidence, Effort) and provide a ranked list with justification for each score.',
  },
];

export const AI_SUGGESTIONS = [
  {
    type: 'refine',
    title: 'Refine your value proposition',
    description: 'Your current value statement could be more specific. Would you like AI to suggest alternatives based on your stakeholder inputs?',
    action: 'Refine with AI',
  },
  {
    type: 'gap',
    title: 'Missing success metrics',
    description: 'No quantitative success metrics have been defined yet. AI can suggest KPIs based on similar AZ initiatives.',
    action: 'Generate metrics',
  },
  {
    type: 'risk',
    title: 'Dependency risk detected',
    description: 'This initiative may depend on the Clinical Data Platform team. Consider scheduling an alignment meeting.',
    action: 'View details',
  },
];
