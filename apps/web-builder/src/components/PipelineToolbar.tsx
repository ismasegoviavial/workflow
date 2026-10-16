import React from 'react';
import { 
  Plus, 
  Save, 
  Download, 
  Sparkles, 
  Trash2, 
  RotateCcw,
  Workflow
} from 'lucide-react';

interface PipelineToolbarProps {
  pipelineName: string;
  pipelineDescription: string;
  onNameChange: (name: string) => void;
  onDescriptionChange: (desc: string) => void;
  onSave: () => void;
  onDeploy: () => void;
  onExport: () => void;
  onQuickAdd: () => void;
  onAutoLayout: () => void;
  onClearAll: () => void;
  onLoadExample: () => void;
  saving?: boolean;
}

export const PipelineToolbar: React.FC<PipelineToolbarProps> = ({
  pipelineName,
  pipelineDescription,
  onNameChange,
  onDescriptionChange,
  onSave,
  onDeploy,
  onExport,
  onQuickAdd,
  onAutoLayout,
  onClearAll,
  onLoadExample,
  saving = false
}) => {
  return (
    <div className="h-13 bg-white border-b border-gray-200 px-4 flex items-center justify-between shadow-xs select-none z-20">
      {/* Left: Brand Icon + Title & Description Input */}
      <div className="flex items-center space-x-3 flex-1 min-w-0">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs flex-shrink-0">
          <Workflow className="w-4 h-4" />
        </div>

        <div className="flex items-center space-x-2 flex-1 min-w-0">
          <div className="flex flex-col min-w-0 flex-1 max-w-md">
            <input
              type="text"
              value={pipelineName}
              onChange={(e) => onNameChange(e.target.value)}
              placeholder="Nombre del Proceso..."
              className="text-sm font-bold text-gray-800 placeholder-gray-400 bg-transparent border-0 hover:bg-gray-50 focus:bg-white focus:ring-1 focus:ring-blue-500 rounded px-2 py-0.5 outline-none transition-all truncate"
            />
            <input
              type="text"
              value={pipelineDescription}
              onChange={(e) => onDescriptionChange(e.target.value)}
              placeholder="Descripción breve del flujo de trabajo..."
              className="text-[11px] text-gray-500 placeholder-gray-400 bg-transparent border-0 hover:bg-gray-50 focus:bg-white focus:ring-1 focus:ring-blue-500 rounded px-2 py-0 outline-none transition-all truncate"
            />
          </div>
        </div>
      </div>

      {/* Right: Functional Action Buttons */}
      <div className="flex items-center space-x-1.5">
        <button
          onClick={onQuickAdd}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 rounded-md text-xs font-semibold transition-colors"
          title="Agregar nueva etapa al flujo"
        >
          <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Nueva Etapa</span>
        </button>

        <button
          onClick={onAutoLayout}
          className="flex items-center space-x-1 px-2.5 py-1.5 bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200 rounded-md text-xs font-medium transition-colors"
          title="Reorganizar nodos en orden secuencial"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Ordenar</span>
        </button>

        <button
          onClick={onLoadExample}
          className="flex items-center space-x-1 px-2.5 py-1.5 bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200 rounded-md text-xs font-medium transition-colors"
          title="Cargar un flujo modelo de ejemplo"
        >
          <RotateCcw className="w-3.5 h-3.5 text-blue-600" />
          <span>Cargar Ejemplo</span>
        </button>

        <button
          onClick={onClearAll}
          className="flex items-center space-x-1 px-2.5 py-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 rounded-md text-xs font-medium transition-colors"
          title="Vaciar todo el lienzo y comenzar en blanco"
        >
          <Trash2 className="w-3.5 h-3.5 text-red-500" />
          <span>Vaciar Todo</span>
        </button>

        <div className="h-5 w-px bg-gray-200 mx-1" />

        <button 
          onClick={onSave}
          disabled={saving}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
          title="Guardar el estado del flujo"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{saving ? 'Guardando...' : 'Guardar Flujo'}</span>
        </button>

        <button 
          onClick={onExport}
          className="flex items-center space-x-1 px-2.5 py-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md text-xs font-medium transition-colors"
          title="Exportar definición JSON"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Exportar</span>
        </button>
      </div>
    </div>
  );
};
