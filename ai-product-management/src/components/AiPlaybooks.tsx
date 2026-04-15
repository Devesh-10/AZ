import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Zap,
  ChevronRight,
  Check,
  Play,
  Clock,
  Sparkles,
  BarChart3,
  Users,
  Rocket,
  Shield,
  Copy,
  Info,
} from 'lucide-react';

interface AiPlaybooksProps {
  onBack: () => void;
  onOpenAiWithPrompt?: (prompt: string) => void;
}

const playbooks = [
  {
    id: 'quarterly-planning',
    title: 'Quarterly Planning',
    description: 'A structured 5-step workflow to plan your next quarter — from reviewing portfolio health to setting priorities and communicating the plan.',
    icon: BarChart3,
    color: '#6C3483',
    duration: '~45 min',
    steps: 5,
    difficulty: 'Standard',
    tags: ['Strategy', 'Planning', 'Alignment'],
    workflow: [
      {
        title: 'Review Portfolio Health',
        description: 'AI analyses all active initiatives and generates a health report with trends, risks, and velocity metrics.',
        aiAction: 'Auto-generate portfolio health report',
        prompt: 'Analyse all active initiatives. For each, provide: health score (0-100), current milestone, risks, blockers, and velocity trend. Summarise portfolio-level patterns.',
        status: 'ready' as const,
      },
      {
        title: 'Score & Prioritise Initiatives',
        description: 'Apply RICE scoring framework to all candidate initiatives using AI-assisted estimation.',
        aiAction: 'Run RICE scoring across candidates',
        prompt: 'For each initiative candidate, estimate Reach (users affected per quarter), Impact (1-3), Confidence (%), and Effort (person-weeks). Calculate RICE scores and provide a ranked list.',
        status: 'ready' as const,
      },
      {
        title: 'Identify Dependencies & Risks',
        description: 'AI maps cross-initiative dependencies and surfaces systemic risks across the portfolio.',
        aiAction: 'Generate dependency map and risk register',
        prompt: 'Review all prioritised initiatives. Identify: (1) cross-initiative dependencies, (2) shared resource conflicts, (3) external dependencies (platform teams, vendors), (4) top 5 portfolio-level risks with mitigations.',
        status: 'ready' as const,
      },
      {
        title: 'Draft Resource Allocation',
        description: 'AI suggests team allocation across initiatives based on priorities, capacity, and skill requirements.',
        aiAction: 'Suggest resource allocation plan',
        prompt: 'Based on the prioritised initiatives and team capacity (12 FTEs across 3 teams), suggest an allocation plan. Flag any capacity conflicts or skill gaps.',
        status: 'ready' as const,
      },
      {
        title: 'Generate Stakeholder Communication',
        description: 'AI drafts a quarterly plan summary tailored for executive stakeholders.',
        aiAction: 'Draft quarterly plan summary',
        prompt: 'Draft a 1-page quarterly plan summary for executive stakeholders. Include: strategic priorities, initiative rankings with rationale, resource allocation, key risks, and success metrics. Use clear, executive-friendly language.',
        status: 'ready' as const,
      },
    ],
  },
  {
    id: 'initiative-launch',
    title: 'Initiative Launch',
    description: 'A comprehensive 7-step playbook for taking a new initiative from approved brief to launch readiness — with AI assistance at each stage.',
    icon: Rocket,
    color: '#8B1A3A',
    duration: '~2 hours',
    steps: 7,
    difficulty: 'Comprehensive',
    tags: ['Launch', 'Execution', 'Go-Live'],
    workflow: [
      {
        title: 'Validate Brief Completeness',
        description: 'AI reviews your product brief for completeness against AZ standards and flags gaps.',
        aiAction: 'Audit product brief',
        prompt: 'Review this product brief against the AZ standard template. Flag: (1) missing sections, (2) ambiguous requirements, (3) undefined success criteria, (4) missing stakeholder sign-offs. Rate completeness as a percentage.',
        status: 'ready' as const,
      },
      {
        title: 'Generate Delivery Milestones',
        description: 'AI creates a phased delivery plan with milestones, dates, and owner assignments.',
        aiAction: 'Draft milestone plan',
        prompt: 'Based on this product brief, generate a delivery plan with 5-8 milestones. For each: title, target date (relative), dependencies, acceptance criteria, and suggested owner role.',
        status: 'ready' as const,
      },
      {
        title: 'Stakeholder Mapping',
        description: 'AI identifies and categorises all stakeholders with a RACI matrix.',
        aiAction: 'Generate RACI matrix',
        prompt: 'Based on the initiative scope, identify all likely stakeholders. Generate a RACI matrix (Responsible, Accountable, Consulted, Informed) for each delivery milestone.',
        status: 'ready' as const,
      },
      {
        title: 'Risk Assessment',
        description: 'AI conducts a structured risk assessment using pharma-specific risk categories.',
        aiAction: 'Run risk assessment',
        prompt: 'Conduct a risk assessment for this initiative. Use categories: Technical, Regulatory/Compliance, Organisational, Data, Integration, Resource. For each risk: description, likelihood (1-5), impact (1-5), mitigation strategy, owner.',
        status: 'ready' as const,
      },
      {
        title: 'Draft Communications Plan',
        description: 'AI generates a communications plan for internal launch activities.',
        aiAction: 'Draft comms plan',
        prompt: 'Draft a communications plan for the initiative launch. Include: stakeholder audiences, key messages by audience, communication channels, frequency, and timeline aligned to delivery milestones.',
        status: 'ready' as const,
      },
      {
        title: 'Create Readiness Checklist',
        description: 'AI compiles a go/no-go checklist with success criteria for launch.',
        aiAction: 'Generate launch checklist',
        prompt: 'Create a launch readiness checklist with go/no-go criteria. Categories: Technical readiness, User acceptance, Documentation, Training, Support, Compliance, Stakeholder approval. Include owner and due date for each item.',
        status: 'ready' as const,
      },
      {
        title: 'Generate Launch Brief',
        description: 'AI compiles all outputs into a comprehensive launch brief for final sign-off.',
        aiAction: 'Compile launch brief',
        prompt: 'Compile all previous outputs (milestone plan, RACI, risk assessment, comms plan, readiness checklist) into a structured launch brief document. Add an executive summary and recommendations section.',
        status: 'ready' as const,
      },
    ],
  },
  {
    id: 'stakeholder-alignment',
    title: 'Stakeholder Alignment',
    description: 'A focused 4-step playbook for achieving and measuring stakeholder alignment on a specific initiative or decision.',
    icon: Users,
    color: '#148F77',
    duration: '~30 min',
    steps: 4,
    difficulty: 'Focused',
    tags: ['Stakeholders', 'Alignment', 'Communication'],
    workflow: [
      {
        title: 'Map Stakeholder Landscape',
        description: 'Identify all stakeholders, their interests, influence level, and current alignment.',
        aiAction: 'Generate stakeholder map',
        prompt: 'For this initiative, identify all stakeholders. For each: name/role, interest in the initiative, influence level (high/medium/low), current alignment (supportive/neutral/resistant), and key concerns.',
        status: 'ready' as const,
      },
      {
        title: 'Generate Tailored Messaging',
        description: 'AI drafts personalised communication for each stakeholder group.',
        aiAction: 'Draft stakeholder messages',
        prompt: 'Draft tailored messages for each stakeholder group identified. Each message should: address their specific concerns, highlight benefits relevant to their role, use appropriate tone (executive vs technical), and include a clear ask.',
        status: 'ready' as const,
      },
      {
        title: 'Prepare Alignment Meeting',
        description: 'AI generates an agenda, pre-read materials, and discussion prompts.',
        aiAction: 'Create meeting materials',
        prompt: 'Create materials for a stakeholder alignment meeting: (1) 60-minute agenda with time allocations, (2) 1-page pre-read summary, (3) discussion questions for each agenda item, (4) decision framework for resolving disagreements.',
        status: 'ready' as const,
      },
      {
        title: 'Track Alignment Score',
        description: 'AI establishes an alignment tracking framework with follow-up actions.',
        aiAction: 'Setup alignment tracking',
        prompt: 'Create an alignment tracking framework: (1) alignment score per stakeholder (1-5 scale), (2) open concerns register, (3) action items with owners, (4) follow-up schedule, (5) escalation criteria if alignment drops below threshold.',
        status: 'ready' as const,
      },
    ],
  },
  {
    id: 'compliance-review',
    title: 'Compliance & Governance Review',
    description: 'A 4-step playbook ensuring your initiative meets AstraZeneca compliance and governance requirements before proceeding.',
    icon: Shield,
    color: '#C4972F',
    duration: '~35 min',
    steps: 4,
    difficulty: 'Standard',
    tags: ['Compliance', 'Governance', 'Regulatory'],
    workflow: [
      {
        title: 'Identify Applicable Regulations',
        description: 'AI reviews the initiative scope and identifies relevant regulatory and compliance requirements.',
        aiAction: 'Map regulatory requirements',
        prompt: 'Review this initiative description and identify all potentially applicable regulations, compliance frameworks, and internal governance policies. Categories: GxP, Data Privacy (GDPR/HIPAA), Information Security, SOX, internal AZ policies.',
        status: 'ready' as const,
      },
      {
        title: 'Gap Analysis',
        description: 'AI compares current initiative state against compliance requirements.',
        aiAction: 'Run compliance gap analysis',
        prompt: 'For each identified regulation/policy, assess the current initiative state. Flag: (1) requirements already met, (2) gaps requiring action, (3) unclear areas needing expert review. Prioritise gaps by risk level.',
        status: 'ready' as const,
      },
      {
        title: 'Generate Remediation Plan',
        description: 'AI creates an action plan to address compliance gaps.',
        aiAction: 'Draft remediation plan',
        prompt: 'For each compliance gap identified, provide: (1) specific action to close the gap, (2) responsible team/role, (3) estimated effort, (4) deadline, (5) verification criteria. Prioritise by risk and effort.',
        status: 'ready' as const,
      },
      {
        title: 'Draft Governance Submission',
        description: 'AI prepares the governance submission document for review boards.',
        aiAction: 'Prepare submission',
        prompt: 'Draft a governance review submission document. Include: initiative summary, compliance assessment results, remediation plan summary, risk acceptance recommendations, and required approvals. Format for the AZ governance review board.',
        status: 'ready' as const,
      },
    ],
  },
];

export default function AiPlaybooks({ onBack, onOpenAiWithPrompt }: AiPlaybooksProps) {
  const [selectedPlaybook, setSelectedPlaybook] = useState<string | null>(null);
  const [copiedPrompt, setCopiedPrompt] = useState<number | null>(null);

  const selected = playbooks.find((p) => p.id === selectedPlaybook);

  const handleCopyPrompt = (prompt: string, index: number) => {
    navigator.clipboard.writeText(prompt);
    setCopiedPrompt(index);
    setTimeout(() => setCopiedPrompt(null), 2000);
  };

  if (selected) {
    return (
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => setSelectedPlaybook(null)}
          className="flex items-center gap-2 text-sm text-az-text-secondary hover:text-az-plum transition-colors mb-6"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Playbooks
        </button>

        {/* Playbook Header */}
        <div className="flex items-start gap-4 mb-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: `${selected.color}12` }}
          >
            <selected.icon className="w-6 h-6" style={{ color: selected.color }} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-az-text">{selected.title} Playbook</h1>
              <span className="px-2 py-0.5 rounded-lg bg-az-purple/8 text-az-purple text-xs font-semibold">
                {selected.steps} Steps
              </span>
            </div>
            <p className="text-sm text-az-text-secondary mt-1">{selected.description}</p>
            <div className="flex items-center gap-4 mt-3 text-xs text-az-text-tertiary">
              <span className="flex items-center gap-1.5"><Clock className="w-3 h-3" /> {selected.duration}</span>
              <span className="flex items-center gap-1.5"><Zap className="w-3 h-3" /> {selected.difficulty}</span>
            </div>
          </div>
          <button
            onClick={() => onOpenAiWithPrompt?.(selected.workflow[0].prompt)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-az-plum text-white text-sm font-semibold hover:bg-az-plum-light transition-colors shadow-sm">
            <Play className="w-4 h-4" />
            Run Step 1
          </button>
        </div>

        {/* Workflow Steps */}
        <div className="space-y-4">
          {selected.workflow.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.05 * index }}
              className="bg-white rounded-xl border border-az-border overflow-hidden"
            >
              <div className="p-5">
                <div className="flex items-start gap-4">
                  {/* Step number */}
                  <div className="w-9 h-9 rounded-full bg-az-plum flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-white">{index + 1}</span>
                  </div>

                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-az-text">{step.title}</h4>
                    <p className="text-xs text-az-text-secondary mt-1 leading-relaxed">{step.description}</p>

                    {/* AI Action */}
                    <div className="mt-3 flex items-center gap-2">
                      <button
                        onClick={() => onOpenAiWithPrompt?.(step.prompt)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-az-purple/5 border border-az-purple/10 hover:bg-az-purple/10 hover:border-az-purple/20 transition-all cursor-pointer"
                      >
                        <Sparkles className="w-3 h-3 text-az-purple" />
                        <span className="text-xs font-medium text-az-purple">{step.aiAction}</span>
                      </button>
                    </div>

                    {/* Prompt */}
                    <div className="mt-3 bg-az-surface-warm rounded-lg border border-az-border-light p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-semibold text-az-text-tertiary uppercase tracking-wider">AI Prompt</span>
                        <button
                          onClick={() => handleCopyPrompt(step.prompt, index)}
                          className="flex items-center gap-1 px-2 py-1 rounded-md bg-white border border-az-border text-[10px] font-medium text-az-text-secondary hover:border-az-purple/20 transition-all"
                        >
                          {copiedPrompt === index ? <Check className="w-3 h-3 text-az-teal" /> : <Copy className="w-3 h-3" />}
                          {copiedPrompt === index ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                      <p className="text-xs text-az-text-secondary leading-relaxed italic">"{step.prompt}"</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step connector */}
              {index < selected.workflow.length - 1 && (
                <div className="flex justify-center -mb-2">
                  <div className="w-px h-4 bg-az-border" />
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Playbook info */}
        <div className="mt-6 bg-az-surface-warm rounded-xl border border-az-border-light p-4 flex items-start gap-3">
          <Info className="w-4 h-4 text-az-text-tertiary flex-shrink-0 mt-0.5" />
          <p className="text-xs text-az-text-secondary leading-relaxed">
            Each step builds on the previous one. AI prompts are pre-configured with your initiative context. You can customise any prompt before running it. All AI outputs include evidence citations for traceability.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-az-text-secondary hover:text-az-plum transition-colors mb-6"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Home
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-az-text">AI Playbooks</h1>
          <p className="text-sm text-az-text-secondary mt-1">
            Multi-step AI-guided workflows for common product management activities. Each playbook provides structured prompts, evidence-based outputs, and audit-ready documentation.
          </p>
        </div>
      </div>

      {/* Playbook Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {playbooks.map((playbook, index) => (
          <motion.button
            key={playbook.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.05 * index }}
            whileHover={{ y: -3 }}
            onClick={() => setSelectedPlaybook(playbook.id)}
            className="group bg-white rounded-xl border border-az-border hover:border-transparent hover:shadow-lg text-left p-6 transition-all duration-300 overflow-hidden relative"
          >
            <div className="absolute inset-0 opacity-0 group-hover:opacity-[0.03] transition-opacity"
              style={{ background: `linear-gradient(135deg, ${playbook.color}, transparent)` }}
            />

            <div className="relative z-10">
              <div className="flex items-start justify-between mb-4">
                <div
                  className="w-11 h-11 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: `${playbook.color}12` }}
                >
                  <playbook.icon className="w-5 h-5" style={{ color: playbook.color }} />
                </div>
                <div className="flex items-center gap-2 text-xs text-az-text-tertiary">
                  <Clock className="w-3 h-3" />
                  {playbook.duration}
                </div>
              </div>

              <h3 className="text-base font-semibold text-az-text group-hover:text-az-plum transition-colors">
                {playbook.title}
              </h3>
              <p className="text-xs text-az-text-tertiary mt-2 leading-relaxed line-clamp-2">
                {playbook.description}
              </p>

              <div className="flex items-center gap-2 mt-4">
                <span className="px-2 py-0.5 rounded-md bg-az-purple/6 text-az-purple text-[10px] font-semibold">
                  {playbook.steps} Steps
                </span>
                <span className="px-2 py-0.5 rounded-md bg-az-surface-warm text-az-text-tertiary text-[10px] font-medium">
                  {playbook.difficulty}
                </span>
              </div>

              <div className="flex items-center gap-1.5 mt-4">
                {playbook.tags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 rounded-full bg-az-surface-warm text-[10px] text-az-text-tertiary">
                    {tag}
                  </span>
                ))}
              </div>

              <div className="mt-4 pt-3 border-t border-az-border-light flex items-center gap-1.5 text-xs font-medium text-az-purple opacity-0 group-hover:opacity-100 transition-opacity">
                View playbook
                <ChevronRight className="w-3 h-3" />
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
