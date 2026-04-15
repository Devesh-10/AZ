import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  ArrowRight,
  ArrowLeft,
  Upload,
  FileText,
  Lightbulb,
  Target,
  Sparkles,
  Check,
  Loader2,
} from 'lucide-react';

interface NewProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateProject?: (name: string, description: string, category: string) => void;
}

const steps = [
  { id: 1, title: 'Name & Describe', icon: Lightbulb },
  { id: 2, title: 'Strategic Context', icon: Target },
  { id: 3, title: 'Upload Inputs', icon: Upload },
  { id: 4, title: 'AI Setup', icon: Sparkles },
];

export default function NewProjectModal({ isOpen, onClose, onCreateProject }: NewProjectModalProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  if (!isOpen) return null;

  const handleNext = () => {
    if (currentStep < 4) setCurrentStep(currentStep + 1);
    if (currentStep === 4) {
      setIsGenerating(true);
      setTimeout(() => {
        setIsGenerating(false);
        if (onCreateProject) {
          onCreateProject(projectName || 'Untitled Initiative', description || 'A new product initiative.', category || 'R&D Technology');
        }
        onClose();
        setCurrentStep(1);
        setProjectName('');
        setDescription('');
        setCategory('');
      }, 2000);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-5 border-b border-az-border">
                <div>
                  <h2 className="text-lg font-semibold text-az-text">Create New Initiative</h2>
                  <p className="text-sm text-az-text-tertiary mt-0.5">Set up your project workspace with AI guidance</p>
                </div>
                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-az-text-tertiary hover:bg-az-surface-warm hover:text-az-text-secondary transition-all"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Step indicator */}
              <div className="px-6 py-4 bg-az-surface-warm border-b border-az-border-light">
                <div className="flex items-center gap-1">
                  {steps.map((step, index) => (
                    <div key={step.id} className="flex items-center flex-1">
                      <div className={`flex items-center gap-2 ${currentStep >= step.id ? 'text-az-plum' : 'text-az-text-tertiary'}`}>
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all
                          ${currentStep > step.id
                            ? 'bg-az-plum text-white'
                            : currentStep === step.id
                              ? 'bg-az-plum text-white ring-4 ring-az-plum/10'
                              : 'bg-az-border text-az-text-tertiary'
                          }`}
                        >
                          {currentStep > step.id ? <Check className="w-3.5 h-3.5" /> : step.id}
                        </div>
                        <span className="text-xs font-medium hidden md:block">{step.title}</span>
                      </div>
                      {index < steps.length - 1 && (
                        <div className={`flex-1 h-px mx-3 ${currentStep > step.id ? 'bg-az-plum' : 'bg-az-border'}`} />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Content */}
              <div className="px-6 py-6 min-h-[300px]">
                <AnimatePresence mode="wait">
                  {currentStep === 1 && (
                    <motion.div
                      key="step1"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-5"
                    >
                      <div>
                        <label className="block text-sm font-medium text-az-text mb-2">Initiative name</label>
                        <input
                          type="text"
                          value={projectName}
                          onChange={(e) => setProjectName(e.target.value)}
                          placeholder="e.g., SOP Assistant, Clinical Trial Dashboard"
                          className="w-full px-4 py-3 rounded-xl border border-az-border bg-white text-sm text-az-text placeholder:text-az-text-tertiary focus:border-az-purple/40 focus:ring-2 focus:ring-az-purple/10 outline-none transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-az-text mb-2">Brief description</label>
                        <textarea
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                          placeholder="What problem does this solve? Who benefits?"
                          rows={4}
                          className="w-full px-4 py-3 rounded-xl border border-az-border bg-white text-sm text-az-text placeholder:text-az-text-tertiary focus:border-az-purple/40 focus:ring-2 focus:ring-az-purple/10 outline-none transition-all resize-none"
                        />
                      </div>
                      <div className="bg-az-purple/5 rounded-xl p-4 border border-az-purple/10">
                        <div className="flex items-start gap-3">
                          <Sparkles className="w-4 h-4 text-az-purple mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-xs font-medium text-az-purple">AI Tip</p>
                            <p className="text-xs text-az-text-secondary mt-1">
                              Don't worry about perfecting the description. AI can help refine it later based on your stakeholder inputs and research.
                            </p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {currentStep === 2 && (
                    <motion.div
                      key="step2"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-5"
                    >
                      <div>
                        <label className="block text-sm font-medium text-az-text mb-2">Category</label>
                        <div className="grid grid-cols-2 gap-3">
                          {['Clinical Operations', 'R&D Technology', 'Commercial Excellence', 'Supply & Manufacturing'].map((cat) => (
                            <button
                              key={cat}
                              onClick={() => setCategory(cat)}
                              className={`px-4 py-3 rounded-xl border text-sm text-left transition-all
                                ${category === cat
                                  ? 'border-az-purple bg-az-purple/5 text-az-plum font-medium'
                                  : 'border-az-border text-az-text-secondary hover:border-az-purple/20'
                                }`}
                            >
                              {cat}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-az-text mb-2">Strategic alignment</label>
                        <div className="space-y-2">
                          {['Patient Outcomes', 'Operational Efficiency', 'Digital Transformation', 'Sustainability'].map((priority) => (
                            <label key={priority} className="flex items-center gap-3 px-4 py-3 rounded-xl border border-az-border hover:border-az-purple/20 cursor-pointer transition-all">
                              <input type="checkbox" className="w-4 h-4 rounded border-az-border text-az-purple focus:ring-az-purple/20" />
                              <span className="text-sm text-az-text">{priority}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {currentStep === 3 && (
                    <motion.div
                      key="step3"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-5"
                    >
                      <div className="border-2 border-dashed border-az-border rounded-2xl p-10 text-center hover:border-az-purple/30 transition-colors cursor-pointer">
                        <Upload className="w-10 h-10 text-az-text-tertiary mx-auto mb-3" />
                        <p className="text-sm font-medium text-az-text">Drop files here or click to upload</p>
                        <p className="text-xs text-az-text-tertiary mt-1">
                          Meeting transcripts, briefs, notes, or any supporting documents
                        </p>
                        <p className="text-xs text-az-text-tertiary mt-2">PDF, DOCX, TXT, PPTX — up to 50MB</p>
                      </div>

                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider">Or start from</p>
                        <div className="grid grid-cols-2 gap-3">
                          <button className="flex items-center gap-3 px-4 py-3 rounded-xl border border-az-border hover:border-az-purple/20 text-left transition-all">
                            <FileText className="w-5 h-5 text-az-purple" />
                            <div>
                              <p className="text-sm font-medium text-az-text">Blank template</p>
                              <p className="text-xs text-az-text-tertiary">Start from scratch</p>
                            </div>
                          </button>
                          <button className="flex items-center gap-3 px-4 py-3 rounded-xl border border-az-border hover:border-az-purple/20 text-left transition-all">
                            <Sparkles className="w-5 h-5 text-az-gold" />
                            <div>
                              <p className="text-sm font-medium text-az-text">AI-generated brief</p>
                              <p className="text-xs text-az-text-tertiary">From your description</p>
                            </div>
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {currentStep === 4 && (
                    <motion.div
                      key="step4"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-5"
                    >
                      {isGenerating ? (
                        <div className="flex flex-col items-center justify-center py-16">
                          <Loader2 className="w-10 h-10 text-az-purple animate-spin mb-4" />
                          <p className="text-sm font-medium text-az-text">Setting up your workspace...</p>
                          <p className="text-xs text-az-text-tertiary mt-1">AI is generating your initial project structure</p>
                        </div>
                      ) : (
                        <>
                          <div className="bg-gradient-to-br from-az-plum/5 to-az-purple/5 rounded-2xl p-6 border border-az-plum/10">
                            <div className="flex items-center gap-3 mb-4">
                              <Sparkles className="w-5 h-5 text-az-purple" />
                              <h3 className="text-sm font-semibold text-az-text">AI will help you with</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                              {[
                                'Generate milestone plan',
                                'Draft initial brief',
                                'Identify stakeholders',
                                'Surface common risks',
                                'Suggest success metrics',
                                'Create task checklist',
                              ].map((item) => (
                                <div key={item} className="flex items-center gap-2 text-sm text-az-text-secondary">
                                  <Check className="w-3.5 h-3.5 text-az-teal flex-shrink-0" />
                                  <span>{item}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="bg-az-surface-warm rounded-xl p-4">
                            <p className="text-xs text-az-text-secondary leading-relaxed">
                              Your project workspace will be created with a SharePoint folder,
                              AI task checklist, and milestone tracking. You can customise
                              everything after setup.
                            </p>
                          </div>
                        </>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-az-border bg-az-surface/50">
                <button
                  onClick={currentStep === 1 ? onClose : handleBack}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-az-text-secondary hover:bg-az-surface-warm transition-all"
                >
                  {currentStep === 1 ? 'Cancel' : <><ArrowLeft className="w-3.5 h-3.5" /> Back</>}
                </button>
                <button
                  onClick={handleNext}
                  disabled={isGenerating}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-az-plum hover:bg-az-plum-light disabled:opacity-50 transition-all shadow-sm"
                >
                  {currentStep === 4 ? (
                    isGenerating ? 'Creating...' : 'Create Project'
                  ) : (
                    <>Continue <ArrowRight className="w-3.5 h-3.5" /></>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
