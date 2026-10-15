import React, { useState } from 'react';
import { 
  Eye, 
  Sliders, 
  Save, 
  Send, 
  Download, 
  Upload, 
  CheckCircle2, 
  ChevronDown,
  Layers
} from 'lucide-react';

interface PipelineToolbarProps {
  pipelineName: string;
  pipelineDescription: string;
  onNameChange: (name: string) => void;
  onDescriptionChange: (desc: string) => void;
  onSave: () => void;
  onDeploy: () => void;
  onExport: () => void;
  onPreview: () => void;
  onConfigure: () => void;
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
  onPreview,
  onConfigure,
  saving = false
}) => {
  const [pipelineType, setPipelineType] = useState('Data Pipeline - Batch');

  return (
    <div className="h-14 bg-white border-b border-[#dadce0] px-4 flex items-center justify-between shadow-sm z-20">
      {/* Left: Pipeline Type Select + Title & Description Input */}
      <div className="flex items-center space-x-4 flex-1">
        {/* Type selector pill */}
        <div className="relative">
          <button className="flex items-center space-x-2 bg-[#5f6368] hover:bg-[#494c4f] text-white text-xs font-medium px-3 py-1.5 rounded transition-colors shadow-sm">
            <span>{pipelineType}</span>
            <ChevronDown className="w-3.5 h-3.5 text-gray-300" />
          </button>
        </div>

        {/* Separator icon */}
        <div className="text-gray-300 font-light text-lg">|</div>

        {/* Name and Description Inputs */}
        <div className="flex flex-col flex-1 max-w-xl">
          <input
            type="text"
            value={pipelineName}
            onChange={(e) => onNameChange(e.target.value)}
            placeholder="Name your pipeline"
            className="text-sm font-semibold text-gray-800 placeholder-gray-400 bg-transparent border-0 border-b border-transparent hover:border-gray-300 focus:border-blue-500 focus:ring-0 px-1 py-0.5 transition-all outline-none"
          />
          <input
            type="text"
            value={pipelineDescription}
            onChange={(e) => onDescriptionChange(e.target.value)}
            placeholder="Enter a description for your pipeline"
            className="text-xs text-gray-500 placeholder-gray-400 bg-transparent border-0 border-b border-transparent hover:border-gray-300 focus:border-blue-500 focus:ring-0 px-1 py-0 transition-all outline-none"
          />
        </div>
      </div>

      {/* Right: Cloud Data Fusion Studio Action Buttons */}
      <div className="flex items-center space-x-1 text-gray-600">
        <button 
          onClick={onPreview}
          className="flex flex-col items-center justify-center px-2.5 py-1 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Vista previa del pipeline"
        >
          <Eye className="w-4 h-4 mb-0.5 text-gray-600" />
          <span className="text-[10px] font-medium uppercase tracking-tight">Preview</span>
        </button>

        <button 
          onClick={onConfigure}
          className="flex flex-col items-center justify-center px-2.5 py-1 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Configuraciones generales"
        >
          <Sliders className="w-4 h-4 mb-0.5 text-gray-600" />
          <span className="text-[10px] font-medium uppercase tracking-tight">Configure</span>
        </button>

        <div className="h-6 w-px bg-gray-200 mx-1" />

        <button 
          onClick={onSave}
          disabled={saving}
          className="flex flex-col items-center justify-center px-2.5 py-1 hover:bg-blue-50 hover:text-blue-700 rounded text-gray-700 transition-colors disabled:opacity-50"
          title="Guardar pipeline"
        >
          <Save className="w-4 h-4 mb-0.5 text-blue-600" />
          <span className="text-[10px] font-medium uppercase tracking-tight">
            {saving ? 'Saving...' : 'Save'}
          </span>
        </button>

        <button 
          onClick={onDeploy}
          className="flex flex-col items-center justify-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors shadow-sm ml-1"
          title="Desplegar pipeline en producción"
        >
          <Send className="w-3.5 h-3.5 mb-0.5 text-white" />
          <span className="text-[10px] font-semibold uppercase tracking-tight">Deploy</span>
        </button>

        <div className="h-6 w-px bg-gray-200 mx-1" />

        <button 
          onClick={onExport}
          className="flex flex-col items-center justify-center px-2.5 py-1 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Importar / Exportar JSON"
        >
          <Upload className="w-4 h-4 mb-0.5 text-gray-600" />
          <span className="text-[10px] font-medium uppercase tracking-tight">Export</span>
        </button>
      </div>
    </div>
  );
};
