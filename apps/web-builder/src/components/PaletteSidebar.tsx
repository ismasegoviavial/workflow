import React, { useState } from 'react';
import { 
  Search, 
  Grid, 
  List, 
  ChevronRight, 
  ChevronDown, 
  ChevronLeft,
  Database,
  FileText,
  Cloud,
  Layers,
  Wand2,
  CheckCircle,
  Calculator,
  Mail,
  Smartphone,
  Split,
  AlertTriangle,
  GitFork,
  Cpu,
  Server,
  Zap,
  Globe,
  ShieldCheck,
  UserCheck
} from 'lucide-react';
import { FusionNodeType } from '../types';

export interface PaletteItem {
  id: string;
  name: string;
  category: string;
  nodeType: FusionNodeType;
  serviceKey?: string;
  description: string;
  iconName: string;
}

const PALETTE_DATA: Record<string, PaletteItem[]> = {
  'Source': [
    { id: 'src_portal', name: 'Portal Cliente', category: 'Source', nodeType: 'source', serviceKey: 'SRV_PORTAL_INGEST', description: 'Formulario web de cliente', iconName: 'Globe' },
    { id: 'src_file', name: 'Carga Archivo', category: 'Source', nodeType: 'source', serviceKey: 'SRV_FILE_UPLOAD', description: 'Ingesta de documentos PDF/Excel', iconName: 'FileText' },
    { id: 'src_api', name: 'API REST Ingest', category: 'Source', nodeType: 'source', serviceKey: 'SRV_API_TRIGGER', description: 'Disparador vía webhook o REST', iconName: 'Zap' },
    { id: 'src_db', name: 'Database Source', category: 'Source', nodeType: 'source', serviceKey: 'SRV_DB_READ', description: 'Extracción desde SQL Server / Postgres', iconName: 'Database' },
    { id: 'src_gcs', name: 'GCS File', category: 'Source', nodeType: 'source', serviceKey: 'SRV_GCS_INGEST', description: 'Google Cloud Storage Ingestion', iconName: 'Cloud' }
  ],
  'Transform': [
    { id: 'tr_wrangler', name: 'Wrangler', category: 'Transform', nodeType: 'transform', serviceKey: 'SRV_WRANGLER', description: 'Transformación interactiva de datos', iconName: 'Wand2' },
    { id: 'tr_rut', name: 'Validador RUT', category: 'Transform', nodeType: 'transform', serviceKey: 'SRV_RUT_VALIDATOR', description: 'Validación de dígito verificador y formato chileno', iconName: 'ShieldCheck' },
    { id: 'tr_date', name: 'Calculador Fechas', category: 'Transform', nodeType: 'transform', serviceKey: 'SRV_DATE_CALCULATOR', description: 'Cálculo de plazos, vencimientos y edades', iconName: 'Calculator' },
    { id: 'tr_score', name: 'Evaluador Riesgo', category: 'Transform', nodeType: 'transform', serviceKey: 'SRV_RISK_SCORING', description: 'Evaluación y motor de reglas de score', iconName: 'Cpu' },
    { id: 'tr_operator', name: 'Bandeja Operador', category: 'Transform', nodeType: 'transform', serviceKey: 'SRV_OPERATOR_REVIEW', description: 'Revisión y aprobación manual por analista', iconName: 'UserCheck' },
    { id: 'tr_normalizer', name: 'Normalizador Domicilio', category: 'Transform', nodeType: 'transform', serviceKey: 'SRV_ADDRESS_NORM', description: 'Estandarización de direcciones y comunas', iconName: 'Server' }
  ],
  'Analytics': [
    { id: 'an_credit', name: 'Credit Scoring ML', category: 'Analytics', nodeType: 'transform', serviceKey: 'SRV_ML_CREDIT', description: 'Inferencia de modelo predictivo', iconName: 'Cpu' },
    { id: 'an_rules', name: 'Reglas de Negocio', category: 'Analytics', nodeType: 'transform', serviceKey: 'SRV_BUSINESS_RULES', description: 'Motor declarativo de políticas', iconName: 'Layers' }
  ],
  'Sink': [
    { id: 'sn_bq', name: 'BigQuery', category: 'Sink', nodeType: 'sink', serviceKey: 'SRV_BIGQUERY_SINK', description: 'Almacenamiento analítico en BigQuery', iconName: 'Database' },
    { id: 'sn_email', name: 'Notificador Email', category: 'Sink', nodeType: 'sink', serviceKey: 'SRV_EMAIL_SENDER', description: 'Envío automático de notificaciones por correo', iconName: 'Mail' },
    { id: 'sn_sms', name: 'Notificador SMS', category: 'Sink', nodeType: 'sink', serviceKey: 'SRV_SMS_SENDER', description: 'Envío de alertas SMS / WhatsApp', iconName: 'Smartphone' },
    { id: 'sn_db', name: 'Database Sink', category: 'Sink', nodeType: 'sink', serviceKey: 'SRV_DB_WRITE', description: 'Persistencia en Base de Datos transaccional', iconName: 'Server' }
  ],
  'Conditions and Actions': [
    { id: 'cd_branch', name: 'Bifurcación Condicional', category: 'Conditions and Actions', nodeType: 'condition', serviceKey: 'SRV_BRANCH', description: 'División según regla Si/No', iconName: 'Split' },
    { id: 'cd_parallel', name: 'Bloque Paralelo', category: 'Conditions and Actions', nodeType: 'condition', serviceKey: 'SRV_PARALLEL', description: 'Ejecución simultánea de tareas', iconName: 'GitFork' }
  ],
  'Error Handlers and Alerts': [
    { id: 'err_alert', name: 'Alerta de Error', category: 'Error Handlers and Alerts', nodeType: 'sink', serviceKey: 'SRV_ERROR_HANDLER', description: 'Despacho de alerta por fallo', iconName: 'AlertTriangle' }
  ]
};

const renderIcon = (name: string) => {
  const iconProps = { className: "w-5 h-5 text-blue-600" };
  switch (name) {
    case 'Globe': return <Globe {...iconProps} />;
    case 'FileText': return <FileText {...iconProps} />;
    case 'Zap': return <Zap {...iconProps} />;
    case 'Database': return <Database {...iconProps} />;
    case 'Cloud': return <Cloud {...iconProps} />;
    case 'Wand2': return <Wand2 {...iconProps} />;
    case 'ShieldCheck': return <ShieldCheck {...iconProps} />;
    case 'Calculator': return <Calculator {...iconProps} />;
    case 'Cpu': return <Cpu {...iconProps} />;
    case 'UserCheck': return <UserCheck {...iconProps} />;
    case 'Server': return <Server {...iconProps} />;
    case 'Layers': return <Layers {...iconProps} />;
    case 'Mail': return <Mail {...iconProps} />;
    case 'Smartphone': return <Smartphone {...iconProps} />;
    case 'Split': return <Split {...iconProps} />;
    case 'GitFork': return <GitFork {...iconProps} />;
    case 'AlertTriangle': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
    default: return <Layers {...iconProps} />;
  }
};

interface PaletteSidebarProps {
  onAddNode: (item: PaletteItem) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const PaletteSidebar: React.FC<PaletteSidebarProps> = ({
  onAddNode,
  collapsed,
  onToggleCollapse
}) => {
  const [filterText, setFilterText] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    'Source': true,
    'Transform': true,
    'Analytics': false,
    'Sink': true,
    'Conditions and Actions': false,
    'Error Handlers and Alerts': false
  });

  const toggleSection = (section: string) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const onDragStart = (event: React.DragEvent, item: PaletteItem) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(item));
    event.dataTransfer.effectAllowed = 'move';
  };

  if (collapsed) {
    return (
      <div className="w-9 bg-[#f1f3f4] border-r border-[#dadce0] flex flex-col items-center py-3 select-none">
        <button 
          onClick={onToggleCollapse}
          className="p-1 hover:bg-gray-200 rounded text-gray-600 transition-colors"
          title="Expandir paleta de microservicios"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <aside className="w-72 bg-[#f8f9fa] border-r border-[#dadce0] flex flex-col h-full select-none z-10">
      {/* Top Filter Bar */}
      <div className="p-2 border-b border-[#dadce0] bg-white flex items-center space-x-1.5">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Filter"
            className="w-full pl-8 pr-2 py-1 text-xs bg-[#f1f3f4] hover:bg-[#e8eaed] focus:bg-white border border-transparent focus:border-blue-500 rounded text-gray-800 placeholder-gray-500 outline-none transition-all"
          />
        </div>

        {/* View mode toggle icons */}
        <div className="flex items-center space-x-0.5 text-gray-500">
          <button 
            onClick={() => setViewMode('grid')}
            className={`p-1 rounded ${viewMode === 'grid' ? 'bg-gray-200 text-gray-800' : 'hover:bg-gray-100 text-gray-500'}`}
            title="Vista cuadrícula"
          >
            <Grid className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={() => setViewMode('list')}
            className={`p-1 rounded ${viewMode === 'list' ? 'bg-gray-200 text-gray-800' : 'hover:bg-gray-100 text-gray-500'}`}
            title="Vista lista"
          >
            <List className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={onToggleCollapse}
            className="p-1 hover:bg-gray-100 rounded text-gray-500"
            title="Contraer paleta"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Accordion Categories */}
      <div className="flex-1 overflow-y-auto">
        {Object.entries(PALETTE_DATA).map(([category, items]) => {
          const filteredItems = items.filter(item => 
            item.name.toLowerCase().includes(filterText.toLowerCase()) ||
            item.serviceKey?.toLowerCase().includes(filterText.toLowerCase()) ||
            item.description.toLowerCase().includes(filterText.toLowerCase())
          );

          if (filterText && filteredItems.length === 0) return null;

          const isOpen = openSections[category] || Boolean(filterText);

          return (
            <div key={category} className="border-b border-[#dadce0]">
              {/* Category Header */}
              <button
                onClick={() => toggleSection(category)}
                className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-[#f1f3f4] transition-colors"
              >
                <div className="flex items-center space-x-1.5">
                  {isOpen ? (
                    <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
                  )}
                  <span>{category}</span>
                </div>
                <span className="text-[11px] font-normal text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                  {items.length}
                </span>
              </button>

              {/* Items Grid/List */}
              {isOpen && (
                <div className="p-2 bg-white">
                  {viewMode === 'grid' ? (
                    <div className="grid grid-cols-3 gap-2">
                      {filteredItems.map(item => (
                        <div
                          key={item.id}
                          draggable
                          onDragStart={(e) => onDragStart(e, item)}
                          onClick={() => onAddNode(item)}
                          className="flex flex-col items-center justify-center p-2 rounded-lg border border-transparent hover:border-blue-300 hover:bg-blue-50/60 cursor-pointer transition-all group text-center"
                          title={`${item.name} (${item.serviceKey || ''}): ${item.description}`}
                        >
                          <div className="w-10 h-10 rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform mb-1">
                            {renderIcon(item.iconName)}
                          </div>
                          <span className="text-[11px] font-medium text-gray-700 leading-tight group-hover:text-blue-700 line-clamp-2">
                            {item.name}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-1">
                      {filteredItems.map(item => (
                        <div
                          key={item.id}
                          draggable
                          onDragStart={(e) => onDragStart(e, item)}
                          onClick={() => onAddNode(item)}
                          className="flex items-center space-x-2.5 p-1.5 rounded hover:bg-blue-50 border border-transparent hover:border-blue-200 cursor-pointer transition-colors group"
                        >
                          <div className="w-7 h-7 rounded bg-blue-50 flex items-center justify-center flex-shrink-0">
                            {renderIcon(item.iconName)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-gray-800 group-hover:text-blue-700 truncate">
                              {item.name}
                            </div>
                            <div className="text-[10px] text-gray-400 truncate">
                              {item.serviceKey || item.description}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
};
