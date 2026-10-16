import React from 'react';
import { 
  Plus, 
  Minus, 
  Maximize2, 
  RotateCcw, 
  MapPin
} from 'lucide-react';
import { useReactFlow } from '@xyflow/react';

interface FloatingControlsProps {
  showMinimap: boolean;
  onToggleMinimap: () => void;
}

export const FloatingControls: React.FC<FloatingControlsProps> = ({
  showMinimap,
  onToggleMinimap
}) => {
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  return (
    <div className="absolute top-4 right-4 z-20 flex flex-col space-y-1 bg-white border border-gray-200 rounded-lg shadow-md p-1 select-none text-gray-600">
      <button
        onClick={() => zoomIn({ duration: 250 })}
        className="p-1.5 hover:bg-gray-100 rounded text-gray-700 transition-colors"
        title="Acercar (Zoom In)"
      >
        <Plus className="w-4 h-4" />
      </button>

      <button
        onClick={() => zoomOut({ duration: 250 })}
        className="p-1.5 hover:bg-gray-100 rounded text-gray-700 transition-colors"
        title="Alejar (Zoom Out)"
      >
        <Minus className="w-4 h-4" />
      </button>

      <div className="h-px bg-gray-200 my-0.5" />

      <button
        onClick={() => fitView({ padding: 0.2, duration: 350 })}
        className="p-1.5 hover:bg-gray-100 rounded text-gray-700 transition-colors"
        title="Encuadrar en pantalla"
      >
        <Maximize2 className="w-4 h-4" />
      </button>

      <button
        onClick={onToggleMinimap}
        className={`p-1.5 rounded transition-colors ${showMinimap ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100 text-gray-700'}`}
        title="Mostrar / Ocultar minimapa"
      >
        <MapPin className="w-4 h-4" />
      </button>

      <button
        onClick={() => fitView({ duration: 300 })}
        className="p-1.5 hover:bg-gray-100 rounded text-gray-700 transition-colors"
        title="Restablecer vista"
      >
        <RotateCcw className="w-4 h-4" />
      </button>
    </div>
  );
};
