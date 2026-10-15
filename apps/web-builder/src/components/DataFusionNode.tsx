import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Menu, 
  Trash2, 
  Settings, 
  Layers, 
  ShieldCheck, 
  Calculator, 
  Wand2, 
  Database, 
  Globe, 
  FileText,
  Mail,
  Zap,
  Cpu,
  UserCheck
} from 'lucide-react';
import { FusionNodeData } from '../types';

const getNodeIcon = (serviceKey?: string, nodeType?: string) => {
  const iconClass = "w-4 h-4";
  if (!serviceKey) {
    if (nodeType === 'source') return <Globe className={iconClass} />;
    if (nodeType === 'sink') return <Database className={iconClass} />;
    return <Wand2 className={iconClass} />;
  }

  if (serviceKey.includes('RUT')) return <ShieldCheck className={iconClass} />;
  if (serviceKey.includes('DATE') || serviceKey.includes('CALCULATOR')) return <Calculator className={iconClass} />;
  if (serviceKey.includes('WRANGLER')) return <Wand2 className={iconClass} />;
  if (serviceKey.includes('PORTAL')) return <Globe className={iconClass} />;
  if (serviceKey.includes('FILE')) return <FileText className={iconClass} />;
  if (serviceKey.includes('EMAIL') || serviceKey.includes('SMS')) return <Mail className={iconClass} />;
  if (serviceKey.includes('BIGQUERY') || serviceKey.includes('DB')) return <Database className={iconClass} />;
  if (serviceKey.includes('OPERATOR')) return <UserCheck className={iconClass} />;
  if (serviceKey.includes('RISK') || serviceKey.includes('ML')) return <Cpu className={iconClass} />;
  return <Zap className={iconClass} />;
};

export const DataFusionNode: React.FC<NodeProps> = memo(({ id, data, selected }) => {
  const nodeData = data as unknown as FusionNodeData;
  const isSource = nodeData.nodeType === 'source';
  const isSink = nodeData.nodeType === 'sink';
  const isCondition = nodeData.nodeType === 'condition';

  // Colors matching Google Cloud Data Fusion Studio
  // Source: Green border (#34a853)
  // Transform: Blue border (#1a73e8)
  // Sink: Purple background/border (#7e57c2)
  let borderClasses = "border-2 border-[#1a73e8] bg-white text-gray-800";
  let titleColor = "text-[#1a73e8]";
  let iconBg = "bg-blue-50 text-blue-600 border border-blue-200";

  if (isSource) {
    borderClasses = "border-2 border-[#34a853] bg-white text-gray-800";
    titleColor = "text-[#34a853]";
    iconBg = "bg-emerald-50 text-emerald-600 border border-emerald-200";
  } else if (isSink) {
    borderClasses = "border-2 border-[#7e57c2] bg-[#7e57c2] text-white";
    titleColor = "text-white";
    iconBg = "bg-white/20 text-white border border-white/30";
  } else if (isCondition) {
    borderClasses = "border-2 border-[#ea8600] bg-white text-gray-800";
    titleColor = "text-[#ea8600]";
    iconBg = "bg-amber-50 text-amber-600 border border-amber-200";
  }

  const substagesCount = nodeData.substages ? nodeData.substages.length : 0;

  return (
    <div 
      className={`relative min-w-[200px] max-w-[240px] rounded-sm shadow-md transition-all select-none ${borderClasses} ${
        selected ? 'ring-2 ring-blue-400 ring-offset-2 shadow-xl scale-[1.02]' : 'hover:shadow-lg'
      }`}
      onDoubleClick={() => nodeData.onConfigure && nodeData.onConfigure(id)}
    >
      {/* Input Handle (Left Port) - All except Source */}
      {!isSource && (
        <Handle
          type="target"
          position={Position.Left}
          id="in"
          className="!w-3 !h-3 !bg-[#5f6368] !border-2 !border-white hover:!bg-blue-600 !-left-2 transition-transform"
        />
      )}

      {/* Badge Count (top right, like the yellow '4' in Data Fusion BigQuery) */}
      {nodeData.badgeCount !== undefined && nodeData.badgeCount > 0 && (
        <div className="absolute -top-2 -right-2 bg-amber-400 text-amber-950 font-bold text-[10px] w-5 h-5 rounded flex items-center justify-center shadow">
          {nodeData.badgeCount}
        </div>
      )}

      {/* Card Content Header */}
      <div className="p-3 flex items-start space-x-2.5">
        {/* Left Icon */}
        <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${iconBg}`}>
          {getNodeIcon(nodeData.serviceKey, nodeData.nodeType)}
        </div>

        {/* Title and Subtitle */}
        <div className="flex-1 min-w-0 pr-4">
          <div className={`text-xs font-bold leading-tight truncate ${titleColor}`}>
            {nodeData.label}
          </div>
          <div className={`text-[10px] leading-tight truncate mt-0.5 ${isSink ? 'text-purple-100' : 'text-gray-500'}`}>
            {nodeData.serviceKey || '4.1.5'}
          </div>

          {/* Subetapas pill */}
          <div className="mt-1.5 flex items-center space-x-1">
            <span className={`text-[9px] px-1.5 py-0.2 rounded font-medium ${
              isSink ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-600'
            }`}>
              {substagesCount === 1 ? '1 Subetapa' : `${substagesCount} Subetapas`}
            </span>
          </div>
        </div>
      </div>

      {/* Bottom Ports for Wrangler / Transform: Alert & Error */}
      {!isSource && !isSink && (
        <div className="px-3 pb-2 pt-0 flex items-center justify-between text-[8px] font-semibold text-gray-400 border-t border-gray-100/80">
          <div className="relative flex items-center space-x-1">
            <span>Alert</span>
            <Handle
              type="source"
              position={Position.Bottom}
              id="alert"
              className="!w-2.5 !h-2.5 !bg-amber-500 !border-2 !border-white !left-2 !-bottom-1"
            />
          </div>
          <div className="relative flex items-center space-x-1">
            <span>Error</span>
            <Handle
              type="source"
              position={Position.Bottom}
              id="error"
              className="!w-2.5 !h-2.5 !bg-red-500 !border-2 !border-white !left-2 !-bottom-1"
            />
          </div>
        </div>
      )}

      {/* Bottom right hamburger menu icon ≡ */}
      <button 
        onClick={(e) => {
          e.stopPropagation();
          nodeData.onConfigure && nodeData.onConfigure(id);
        }}
        className={`absolute bottom-1.5 right-1.5 p-1 rounded transition-colors ${
          isSink ? 'hover:bg-white/20 text-white' : 'hover:bg-gray-200 text-gray-500'
        }`}
        title="Configurar Subetapas y Parámetros"
      >
        <Menu className="w-3.5 h-3.5" />
      </button>

      {/* Output Handle (Right Port) - All except Sink */}
      {!isSink && (
        <Handle
          type="source"
          position={Position.Right}
          id="out"
          className="!w-3 !h-3 !bg-[#5f6368] !border-2 !border-white hover:!bg-blue-600 !-right-2 transition-transform"
        />
      )}
    </div>
  );
});
