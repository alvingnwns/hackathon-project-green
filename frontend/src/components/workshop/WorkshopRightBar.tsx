interface WorkshopRightBarProps {
  analysis?: {
    land_size_est?: string;
    building_condition?: string;
    structural_decision?: string;
    reasoning?: string;
  };
  greenSolution?: {
    concept_name?: string;
    description?: string;
    estimated_cost?: number;
    waste_management?: string;
  };
  projectConcept?: string;
  projectCost?: number;
  isBlank?: boolean;
}

export default function WorkshopRightBar({
  analysis,
  greenSolution,
  projectConcept,
  projectCost,
  isBlank = false,
}: WorkshopRightBarProps) {
  return (
    <div className="w-80 overflow-y-auto" style={{ backgroundColor: 'var(--color-surface)' }}>
      <div className="p-6 space-y-6">
        {/* Section 1: Analysis */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--color-brand-green)' }}>
            Analysis
          </h2>
          {isBlank ? (
            <div className="text-sm leading-relaxed italic" style={{ color: 'var(--color-text-secondary)' }}>
              Upload assets to see analysis
            </div>
          ) : (
            <div className="space-y-3">
              <div className="space-y-1">
                <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                  Land size (est)
                </div>
                <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {analysis?.land_size_est}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                  Building condition
                </div>
                <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {analysis?.building_condition}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                  Structural decision
                </div>
                <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {analysis?.structural_decision}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                  Reasoning
                </div>
                <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {analysis?.reasoning}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Section 2: Green Solution - Only show when not blank */}
        {!isBlank && (
          <div className="space-y-4">
            <div className="space-y-0">
              <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                Green Solution
              </div>
              <h3 className="text-xl font-bold tracking-tight" style={{ color: 'var(--color-brand-green)' }}>
                {greenSolution?.concept_name || projectConcept}
              </h3>
            </div>
            <div className="space-y-3">
              <div className="space-y-1">
                <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                  Description
                </div>
                <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {greenSolution?.description}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                  Estimated cost
                </div>
                <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {greenSolution?.estimated_cost?.toLocaleString() || projectCost?.toLocaleString()}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--color-brand-green-light)' }}>
                  Waste management
                </div>
                <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {greenSolution?.waste_management}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
