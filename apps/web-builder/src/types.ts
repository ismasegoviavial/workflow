export type FieldType = 'string' | 'number' | 'date' | 'boolean' | 'file';

export interface SchemaField {
  id: string;
  name: string;
  title: string;
  type: FieldType;
  required: boolean;
  description?: string;
}

export interface Substage {
  id: string;
  substage_key: string;
  title: string;
  is_initial: boolean;
  service_id?: string;
  service_name?: string;
  editor_workspace_group: string;
  reviewer_workspace_group: string;
  fields: SchemaField[];
  output_fields: SchemaField[];
  is_clonable: boolean;
}

export interface Stage {
  id: string;
  stage_key: string;
  title: string;
  is_initial: boolean;
  is_final: boolean;
  substages: Substage[];
}

export interface WorkflowConfig {
  id: string;
  company_id: string;
  company_code: string;
  code: string;
  name: string;
  description: string;
  stages: Stage[];
}

export interface ExecutionState {
  execution_id: string;
  execution_code: string;
  status: 'IN_PROGRESS' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'COMPLETED' | 'ROLLED_BACK';
  current_stage_id: string;
  current_substage_id: string;
  can_rollback: boolean;
  current_payload: Record<string, any>;
  context_data: Record<string, any>;
  iteration: number;
}

export type FusionNodeType = 'source' | 'transform' | 'sink' | 'condition';

export type RuleOperator = '>' | '<' | '>=' | '<=' | '==' | '!=' | 'contains' | 'is_true' | 'is_false';

export interface DecisionRule {
  id: string;
  variable: string;
  operator: RuleOperator;
  value: string;
  branchLabel: string;
  branchKey: string;
  color?: string;
}

export interface DecisionEngineConfig {
  engineType: 'rules' | 'service';
  serviceKey?: string;
  rules: DecisionRule[];
  defaultBranch: {
    branchLabel: string;
    branchKey: string;
    color?: string;
  };
}

export interface FusionNodeData {
  label: string;
  stageKey: string;
  subTitle?: string;
  nodeType: FusionNodeType;
  serviceKey?: string;
  serviceName?: string;
  substages: Substage[];
  decisionConfig?: DecisionEngineConfig;
  badgeCount?: number;
  isInitial?: boolean;
  isFinal?: boolean;
  onConfigure?: (nodeId: string) => void;
  onDelete?: (nodeId: string) => void;
}
