import React from 'react';
import { 
  Plus, 
  Minus, 
  Maximize2, 
  RotateCcw, 
  Grid3X3, 
  MapPin, 
  MessageSquare,
  Sparkles
} from 'lucide-react';
import { useReactFlow } from '@xyflow/react';

interface FloatingControlsProps {
  onQuickAdd: () => void;
  onAutoLayout: () => void;
  showMinimap: boolean;
  onToggleMinimap: () => void;
}

export const FloatingControls: React.FC<FloatingControlsProps> = ({
  onQuickAdd,
  onAutoLayout,
  showMinimap,
  onToggleMinimap
}) => {
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  return (
    <>
      {/* Top-Right Big Green FAB (+) Button identical to Cloud Data Fusion */}
      <div className="absolute top-4 right-4 z-20">
        <button
          onClick={onQuickAdd}
          className="w-12 h-12 rounded-full bg-[#34a853] hover:bg-[#2d9249] text-white shadow-lg hover:shadow-xl flex items-center justify-center transition-transform hover:scale-105 active:scale-95"
          title="Agregar nueva Etapa al lienzo"
        >
          <Plus className="w-7 h-7 text-white stroke-[2.5]" />
        </button>
      </div>

      {/* Right Vertical Control Strip identical to Cloud Data Fusion Studio */}
      <div className="absolute top-20 right-4 z-20 flex flex-col space-y-1 bg-white border border-[#dadce0] rounded shadow-md p-1 select-none text-gray-600">
        <button
          onClick={() => zoomIn({ duration: 300 })}
          className="p-2 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Acercar (Zoom In)"
        >
          <Plus className="w-4 h-4" />
        </button>

        <button
          onClick={() => zoomOut({ duration: 300 })}
          className="p-2 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Alejar (Zoom Out)"
        >
          <Minus className="w-4 h-4" />
        </button>

        <div className="h-px bg-gray-200 my-0.5" />

        <button
          onClick={() => fitView({ padding: 0.2, duration: 400 })}
          className="p-2 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Ajustar a la pantalla (Fit View)"
        >
          <Maximize2 className="w-4 h-4" />
        </button>

        <button
          onClick={onAutoLayout}
          className="p-2 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Auto-organizar diagrama"
        >
          <Grid3X3 className="w-4 h-4" />
        </button>

        <button
          onClick={onToggleMinimap}
          className={`p-2 rounded transition-colors ${showMinimap ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100 text-gray-700'}`}
          title="Mostrar/Ocultar Minimapa"
        >
          <MapPin className="w-4 h-4" />
        </button>

        <button
          onClick={() => fitView({ duration: 300 })}
          className="p-2 hover:bg-gray-100 rounded text-gray-700 transition-colors"
          title="Centrar lienzo"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </>
  );
};
