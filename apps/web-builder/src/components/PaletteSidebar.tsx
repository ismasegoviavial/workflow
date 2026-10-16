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
  'Orígenes y Entradas': [
    { id: 'src_portal', name: 'Formulario Cliente', category: 'Orígenes y Entradas', nodeType: 'source', serviceKey: 'SRV_PORTAL_INGEST', description: 'Formulario web de autoatención para el cliente', iconName: 'Globe' },
    { id: 'src_file', name: 'Carga de Documentos', category: 'Orígenes y Entradas', nodeType: 'source', serviceKey: 'SRV_FILE_UPLOAD', description: 'Recepción de PDFs, comprobantes o liquidaciones', iconName: 'FileText' },
    { id: 'src_api', name: 'Disparador API REST', category: 'Orígenes y Entradas', nodeType: 'source', serviceKey: 'SRV_API_TRIGGER', description: 'Recepción automática vía webhook o integración', iconName: 'Zap' },
    { id: 'src_db', name: 'Extracción SQL / DB', category: 'Orígenes y Entradas', nodeType: 'source', serviceKey: 'SRV_DB_READ', description: 'Extracción desde base de datos transaccional', iconName: 'Database' },
    { id: 'src_gcs', name: 'Archivos Cloud Storage', category: 'Orígenes y Entradas', nodeType: 'source', serviceKey: 'SRV_GCS_INGEST', description: 'Ingesta de archivos desde Google Cloud Storage', iconName: 'Cloud' }
  ],
  'Microservicios y Validación': [
    { id: 'tr_rut', name: 'Validador de RUT', category: 'Microservicios y Validación', nodeType: 'transform', serviceKey: 'SRV_RUT_VALIDATOR', description: 'Validación de dígito verificador y formato chileno', iconName: 'ShieldCheck' },
    { id: 'tr_date', name: 'Calculador de Fechas', category: 'Microservicios y Validación', nodeType: 'transform', serviceKey: 'SRV_DATE_CALCULATOR', description: 'Cálculo de plazos, vencimientos y edades', iconName: 'Calculator' },
    { id: 'tr_operator', name: 'Bandeja de Analista', category: 'Microservicios y Validación', nodeType: 'transform', serviceKey: 'SRV_OPERATOR_REVIEW', description: 'Revisión y visto bueno manual por un operador', iconName: 'UserCheck' },
    { id: 'tr_normalizer', name: 'Normalizador Domicilio', category: 'Microservicios y Validación', nodeType: 'transform', serviceKey: 'SRV_ADDRESS_NORM', description: 'Estandarización de direcciones y comunas', iconName: 'Server' },
    { id: 'tr_wrangler', name: 'Transformador de Datos', category: 'Microservicios y Validación', nodeType: 'transform', serviceKey: 'SRV_TRANSFORMER', description: 'Limpieza y mapeo estructural de campos', iconName: 'Wand2' }
  ],
  'Motores de Decisión y Reglas': [
    { id: 'an_decision', name: 'Motor de Decisión (Reglas)', category: 'Motores de Decisión y Reglas', nodeType: 'condition', serviceKey: 'SRV_DECISION_ENGINE', description: 'Constructor de reglas condicionales agnósticas (SI / ENTONCES)', iconName: 'Split' },
    { id: 'an_credit', name: 'Motor Scoring de Riesgo', category: 'Motores de Decisión y Reglas', nodeType: 'transform', serviceKey: 'SRV_RISK_SCORING', description: 'Evaluación y scoring crediticio automatizado', iconName: 'Cpu' },
    { id: 'an_rules', name: 'Motor de Políticas', category: 'Motores de Decisión y Reglas', nodeType: 'transform', serviceKey: 'SRV_BUSINESS_RULES', description: 'Evaluación declarativa de reglas comerciales', iconName: 'Layers' }
  ],
  'Destinos y Notificaciones': [
    { id: 'sn_db', name: 'Guardar en Base de Datos', category: 'Destinos y Notificaciones', nodeType: 'sink', serviceKey: 'SRV_DB_WRITE', description: 'Persistencia en Base de Datos transaccional', iconName: 'Server' },
    { id: 'sn_email', name: 'Notificación por Email', category: 'Destinos y Notificaciones', nodeType: 'sink', serviceKey: 'SRV_EMAIL_SENDER', description: 'Envío de confirmación o resoluciones por correo', iconName: 'Mail' },
    { id: 'sn_sms', name: 'Notificación SMS/WhatsApp', category: 'Destinos y Notificaciones', nodeType: 'sink', serviceKey: 'SRV_SMS_SENDER', description: 'Envío de alertas móviles automáticas', iconName: 'Smartphone' },
    { id: 'sn_bq', name: 'Almacén Analítico BigQuery', category: 'Destinos y Notificaciones', nodeType: 'sink', serviceKey: 'SRV_BIGQUERY_SINK', description: 'Persistencia para reportería y analítica gerencial', iconName: 'Database' }
  ],
  'Compuertas y Control de Flujo': [
    { id: 'cd_branch', name: 'Bifurcación (Si / No)', category: 'Compuertas y Control de Flujo', nodeType: 'condition', serviceKey: 'SRV_BRANCH', description: 'División del flujo según condición de negocio', iconName: 'Split' },
    { id: 'cd_parallel', name: 'Ejecución en Paralelo', category: 'Compuertas y Control de Flujo', nodeType: 'condition', serviceKey: 'SRV_PARALLEL', description: 'Ejecución simultánea de tareas independientes', iconName: 'GitFork' }
  ],
  'Excepciones y Alertas': [
    { id: 'err_alert', name: 'Gestor de Alerta / Error', category: 'Excepciones y Alertas', nodeType: 'sink', serviceKey: 'SRV_ERROR_HANDLER', description: 'Notificación inmediata ante fallas o inconsistencias', iconName: 'AlertTriangle' }
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
    'Orígenes y Entradas': true,
    'Microservicios y Validación': true,
    'Motores de Decisión y Reglas': false,
    'Destinos y Notificaciones': true,
    'Compuertas y Control de Flujo': false,
    'Excepciones y Alertas': false
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
          title="Expandir catálogo de componentes"
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
            placeholder="Buscar microservicios y bloques..."
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
            title="Contraer panel"
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
