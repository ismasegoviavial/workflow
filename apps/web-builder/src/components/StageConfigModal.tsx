import React, { useState } from 'react';
import { 
  X, 
  Plus, 
  Trash2, 
  Shield, 
  Cpu, 
  CheckCircle, 
  FileText, 
  Users, 
  ChevronRight,
  Sparkles,
  Settings2
} from 'lucide-react';
import { FusionNodeData, Substage, SchemaField } from '../types';

interface StageConfigModalProps {
  nodeId: string | null;
  initialData: FusionNodeData | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (nodeId: string, updatedData: Partial<FusionNodeData>) => void;
  onDeleteNode: (nodeId: string) => void;
}

const AVAILABLE_SERVICES = [
  { key: 'SRV_RUT_VALIDATOR', name: 'Validador de RUT y Dígito Verificador' },
  { key: 'SRV_DATE_CALCULATOR', name: 'Calculadora de Fechas y Vencimiento' },
  { key: 'SRV_PORTAL_INGEST', name: 'Formulario de Ingesta Portal Cliente' },
  { key: 'SRV_OPERATOR_REVIEW', name: 'Bandeja de Revisión y Dictamen' },
  { key: 'SRV_RISK_SCORING', name: 'Evaluador de Riesgo Crediticio' },
  { key: 'SRV_EMAIL_SENDER', name: 'Notificador por Correo Electrónico' },
  { key: 'SRV_SMS_SENDER', name: 'Notificador SMS / Mensajería' },
  { key: 'SRV_BIGQUERY_SINK', name: 'Persistencia en Google BigQuery' },
  { key: 'SRV_WRANGLER', name: 'Wrangler Data Transform' },
];

export const StageConfigModal: React.FC<StageConfigModalProps> = ({
  nodeId,
  initialData,
  isOpen,
  onClose,
  onSave,
  onDeleteNode
}) => {
  if (!isOpen || !nodeId || !initialData) return null;

  const [label, setLabel] = useState(initialData.label);
  const [stageKey, setStageKey] = useState(initialData.stageKey);
  const [serviceKey, setServiceKey] = useState(initialData.serviceKey || '');
  const [nodeType, setNodeType] = useState(initialData.nodeType);
  const [substages, setSubstages] = useState<Substage[]>(initialData.substages || []);
  const [activeSubstageIndex, setActiveSubstageIndex] = useState<number>(0);

  // Substage helper to add
  const handleAddSubstage = () => {
    const newIdx = substages.length + 1;
    const newSubstage: Substage = {
      id: `sub_${Date.now()}`,
      substage_key: `substage_${newIdx}`,
      title: `Subetapa ${newIdx}`,
      is_initial: substages.length === 0,
      service_id: serviceKey || 'SRV_RUT_VALIDATOR',
      service_name: AVAILABLE_SERVICES.find(s => s.key === serviceKey)?.name || 'Validador',
      editor_workspace_group: 'CLIENTE',
      reviewer_workspace_group: 'OPERADOR',
      fields: [
        { id: `f_${Date.now()}`, name: 'rut', title: 'RUT Cliente', type: 'string', required: true }
      ],
      output_fields: [],
      is_clonable: false
    };
    setSubstages([...substages, newSubstage]);
    setActiveSubstageIndex(substages.length);
  };

  const handleRemoveSubstage = (index: number) => {
    const updated = substages.filter((_, i) => i !== index);
    setSubstages(updated);
    if (activeSubstageIndex >= updated.length) {
      setActiveSubstageIndex(Math.max(0, updated.length - 1));
    }
  };

  const handleUpdateCurrentSubstage = (field: keyof Substage, value: any) => {
    if (substages[activeSubstageIndex]) {
      const updated = [...substages];
      updated[activeSubstageIndex] = {
        ...updated[activeSubstageIndex],
        [field]: value
      };
      setSubstages(updated);
    }
  };

  const handleAddField = () => {
    if (!substages[activeSubstageIndex]) return;
    const currentSub = substages[activeSubstageIndex];
    const newField: SchemaField = {
      id: `f_${Date.now()}`,
      name: `campo_${currentSub.fields.length + 1}`,
      title: `Nuevo Campo ${currentSub.fields.length + 1}`,
      type: 'string',
      required: true
    };
    handleUpdateCurrentSubstage('fields', [...currentSub.fields, newField]);
  };

  const handleRemoveField = (fieldIdx: number) => {
    if (!substages[activeSubstageIndex]) return;
    const currentSub = substages[activeSubstageIndex];
    const updated = currentSub.fields.filter((_, i) => i !== fieldIdx);
    handleUpdateCurrentSubstage('fields', updated);
  };

  const handleFieldChange = (fieldIdx: number, prop: keyof SchemaField, val: any) => {
    if (!substages[activeSubstageIndex]) return;
    const currentSub = substages[activeSubstageIndex];
    const updatedFields = [...currentSub.fields];
    updatedFields[fieldIdx] = {
      ...updatedFields[fieldIdx],
      [prop]: val
    };
    handleUpdateCurrentSubstage('fields', updatedFields);
  };

  const handleSave = () => {
    onSave(nodeId, {
      label,
      stageKey,
      serviceKey,
      nodeType,
      substages
    });
    onClose();
  };

  const currentSubstage = substages[activeSubstageIndex];

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 select-none">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden border border-gray-200">
        
        {/* Header Modal - Google Cloud Style */}
        <div className="bg-[#1a73e8] px-6 py-4 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-white/20 flex items-center justify-center">
              <Settings2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-base font-semibold leading-tight">Configuración de Etapa: {label}</h2>
              <p className="text-xs text-blue-100">Configura subetapas, microservicios, campos dinámicos y roles</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-white/20 rounded-full transition-colors text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* General Settings */}
          <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Nombre de la Etapa
              </label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="w-full px-3 py-1.5 text-xs border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Identificador Único (Key)
              </label>
              <input
                type="text"
                value={stageKey}
                onChange={(e) => setStageKey(e.target.value)}
                className="w-full px-3 py-1.5 text-xs font-mono border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Tipo en Canvas
              </label>
              <select
                value={nodeType}
                onChange={(e) => setNodeType(e.target.value as any)}
                className="w-full px-3 py-1.5 text-xs border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none bg-white"
              >
                <option value="source">Source (Disparador / Entrada)</option>
                <option value="transform">Transform (Microservicio / Proceso)</option>
                <option value="sink">Sink (Salida / Almacenamiento)</option>
                <option value="condition">Condition (Bifurcación / Paralelo)</option>
              </select>
            </div>
          </div>

          {/* Subetapas Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-bold text-gray-800">Subetapas del Proceso</h3>
                <p className="text-xs text-gray-500">Cada subetapa ejecuta un microservicio o solicita campos al usuario</p>
              </div>
              <button
                onClick={handleAddSubstage}
                className="flex items-center space-x-1 px-3 py-1.5 bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 rounded text-xs font-medium transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Agregar Subetapa</span>
              </button>
            </div>

            {/* Substages Navigation Tabs & Detail */}
            <div className="border border-gray-200 rounded-lg overflow-hidden flex min-h-[300px]">
              
              {/* Left List of Subetapas */}
              <div className="w-1/3 bg-gray-50 border-r border-gray-200 p-2 space-y-1">
                {substages.length === 0 ? (
                  <div className="text-center py-8 text-gray-400 text-xs">
                    Sin subetapas. Haz clic en "Agregar Subetapa".
                  </div>
                ) : (
                  substages.map((sub, idx) => (
                    <div
                      key={sub.id || idx}
                      onClick={() => setActiveSubstageIndex(idx)}
                      className={`flex items-center justify-between p-2.5 rounded text-xs cursor-pointer transition-colors ${
                        activeSubstageIndex === idx 
                          ? 'bg-blue-600 text-white font-semibold shadow-xs' 
                          : 'hover:bg-gray-200 text-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-2 truncate">
                        <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] bg-white/20">
                          {idx + 1}
                        </span>
                        <span className="truncate">{sub.title}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveSubstage(idx);
                          }}
                          className={`p-1 rounded hover:bg-black/10 ${
                            activeSubstageIndex === idx ? 'text-white' : 'text-gray-400 hover:text-red-600'
                          }`}
                          title="Eliminar"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                        <ChevronRight className="w-3.5 h-3.5 opacity-60" />
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Right Detail Configuration of Active Substage */}
              <div className="flex-1 p-4 bg-white overflow-y-auto">
                {currentSubstage ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-600 uppercase mb-1">
                          Título de la Subetapa
                        </label>
                        <input
                          type="text"
                          value={currentSubstage.title}
                          onChange={(e) => handleUpdateCurrentSubstage('title', e.target.value)}
                          className="w-full px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:border-blue-500 outline-none"
                        />
                      </div>

                      <div>
                        <label className="block text-[11px] font-semibold text-gray-600 uppercase mb-1">
                          Microservicio Asignado
                        </label>
                        <select
                          value={currentSubstage.service_id || ''}
                          onChange={(e) => {
                            const val = e.target.value;
                            handleUpdateCurrentSubstage('service_id', val);
                            const found = AVAILABLE_SERVICES.find(s => s.key === val);
                            if (found) handleUpdateCurrentSubstage('service_name', found.name);
                          }}
                          className="w-full px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:border-blue-500 outline-none bg-white"
                        >
                          <option value="">(Ninguno / Manual)</option>
                          {AVAILABLE_SERVICES.map(srv => (
                            <option key={srv.key} value={srv.key}>{srv.name} ({srv.key})</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Roles Configuration */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-600 uppercase mb-1">
                          Rol Ejecutor (Quién llena los datos)
                        </label>
                        <select
                          value={currentSubstage.editor_workspace_group || 'CLIENTE'}
                          onChange={(e) => handleUpdateCurrentSubstage('editor_workspace_group', e.target.value)}
                          className="w-full px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:border-blue-500 outline-none bg-white font-medium"
                        >
                          <option value="CLIENTE">CLIENTE (Portal de autoatención)</option>
                          <option value="OPERADOR">OPERADOR (Bandeja interna de analistas)</option>
                          <option value="ADMIN">ADMIN (Supervisión y control)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-[11px] font-semibold text-gray-600 uppercase mb-1">
                          Rol Revisor (Quién autoriza/dictamina)
                        </label>
                        <select
                          value={currentSubstage.reviewer_workspace_group || 'OPERADOR'}
                          onChange={(e) => handleUpdateCurrentSubstage('reviewer_workspace_group', e.target.value)}
                          className="w-full px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:border-blue-500 outline-none bg-white font-medium"
                        >
                          <option value="OPERADOR">OPERADOR</option>
                          <option value="ADMIN">ADMIN</option>
                          <option value="CLIENTE">CLIENTE</option>
                        </select>
                      </div>
                    </div>

                    {/* Form Fields Schema */}
                    <div className="pt-2 border-t border-gray-200">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-gray-700">Campos Solicitados en Formulario</span>
                        <button
                          onClick={handleAddField}
                          className="text-[11px] text-blue-600 hover:text-blue-800 font-semibold flex items-center space-x-1"
                        >
                          <Plus className="w-3 h-3" />
                          <span>Agregar Campo</span>
                        </button>
                      </div>

                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {currentSubstage.fields && currentSubstage.fields.length > 0 ? (
                          currentSubstage.fields.map((field, fIdx) => (
                            <div key={field.id || fIdx} className="flex items-center space-x-2 bg-gray-50 p-2 rounded border border-gray-200 text-xs">
                              <input
                                type="text"
                                value={field.title}
                                placeholder="Etiqueta"
                                onChange={(e) => handleFieldChange(fIdx, 'title', e.target.value)}
                                className="flex-1 px-2 py-1 border border-gray-300 rounded bg-white"
                              />
                              <input
                                type="text"
                                value={field.name}
                                placeholder="variable_key"
                                onChange={(e) => handleFieldChange(fIdx, 'name', e.target.value)}
                                className="w-28 font-mono text-[11px] px-2 py-1 border border-gray-300 rounded bg-white"
                              />
                              <select
                                value={field.type}
                                onChange={(e) => handleFieldChange(fIdx, 'type', e.target.value)}
                                className="w-24 px-1.5 py-1 border border-gray-300 rounded bg-white text-[11px]"
                              >
                                <option value="string">Texto</option>
                                <option value="number">Número</option>
                                <option value="date">Fecha</option>
                                <option value="boolean">Booleano</option>
                                <option value="file">Archivo</option>
                              </select>
                              <label className="flex items-center space-x-1 text-[11px] text-gray-600 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={field.required}
                                  onChange={(e) => handleFieldChange(fIdx, 'required', e.target.checked)}
                                  className="rounded text-blue-600"
                                />
                                <span>Req</span>
                              </label>
                              <button
                                onClick={() => handleRemoveField(fIdx)}
                                className="text-gray-400 hover:text-red-500 p-1"
                                title="Eliminar campo"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          ))
                        ) : (
                          <div className="text-xs text-gray-400 py-3 text-center">
                            No hay campos definidos para esta subetapa.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-400 text-xs">
                    Selecciona o crea una subetapa para ver sus detalles.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="bg-gray-50 px-6 py-3 border-t border-gray-200 flex items-center justify-between">
          <button
            onClick={() => {
              if (confirm(`¿Seguro que deseas eliminar la etapa "${label}"?`)) {
                onDeleteNode(nodeId);
                onClose();
              }
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded font-medium transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Eliminar Etapa del Pipeline</span>
          </button>

          <div className="flex items-center space-x-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 text-xs text-gray-600 hover:text-gray-800 font-medium transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              className="px-5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded shadow-xs transition-colors"
            >
              Guardar Cambios
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
