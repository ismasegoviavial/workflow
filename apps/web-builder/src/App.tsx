import React, { useState, useCallback, useRef } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  MarkerType,
  Connection,
  Edge,
  Node,
  useReactFlow
} from '@xyflow/react';

import { PipelineToolbar } from './components/PipelineToolbar';
import { PaletteSidebar, PaletteItem } from './components/PaletteSidebar';
import { DataFusionNode } from './components/DataFusionNode';
import { StageConfigModal } from './components/StageConfigModal';
import { FloatingControls } from './components/FloatingControls';
import { FusionNodeData, Substage, WorkflowConfig } from './types';

const nodeTypes = {
  dataFusion: DataFusionNode,
};

// Default pipeline stages
const INITIAL_NODES: Node[] = [
  {
    id: 'node-source-1',
    type: 'dataFusion',
    position: { x: 120, y: 180 },
    data: {
      label: 'Ingreso de Solicitud',
      stageKey: 'ingreso_solicitud',
      nodeType: 'source',
      serviceKey: 'SRV_PORTAL_INGEST',
      substages: [
        {
          id: 'sub-1',
          substage_key: 'form_inicial',
          title: 'Formulario Inicial del Cliente',
          is_initial: true,
          service_id: 'SRV_PORTAL_INGEST',
          service_name: 'Formulario Web',
          editor_workspace_group: 'CLIENTE',
          reviewer_workspace_group: 'OPERADOR',
          fields: [
            { id: 'f1', name: 'rut_cliente', title: 'RUT Solicitante', type: 'string', required: true },
            { id: 'f2', name: 'nombre_completo', title: 'Nombre Completo', type: 'string', required: true },
            { id: 'f3', name: 'monto_solicitado', title: 'Monto Solicitado (CLP)', type: 'number', required: true }
          ],
          output_fields: [],
          is_clonable: false
        }
      ]
    }
  },
  {
    id: 'node-transform-2',
    type: 'dataFusion',
    position: { x: 420, y: 200 },
    data: {
      label: 'Admisión y Validación',
      stageKey: 'admision_validaciones',
      nodeType: 'transform',
      serviceKey: 'SRV_RUT_VALIDATOR',
      substages: [
        {
          id: 'sub-2a',
          substage_key: 'val_rut',
          title: 'Validación de RUT y Antecedentes',
          is_initial: false,
          service_id: 'SRV_RUT_VALIDATOR',
          service_name: 'Validador RUT',
          editor_workspace_group: 'OPERADOR',
          reviewer_workspace_group: 'OPERADOR',
          fields: [
            { id: 'f4', name: 'estado_rut', title: 'Dictamen RUT', type: 'string', required: true }
          ],
          output_fields: [],
          is_clonable: false
        },
        {
          id: 'sub-2b',
          substage_key: 'calc_fechas',
          title: 'Cálculo de Plazos y Cuotas',
          is_initial: false,
          service_id: 'SRV_DATE_CALCULATOR',
          service_name: 'Calculador Fechas',
          editor_workspace_group: 'OPERADOR',
          reviewer_workspace_group: 'ADMIN',
          fields: [
            { id: 'f5', name: 'fecha_primer_vencimiento', title: 'Primer Vencimiento', type: 'date', required: true }
          ],
          output_fields: [],
          is_clonable: false
        }
      ]
    }
  },
  {
    id: 'node-sink-3',
    type: 'dataFusion',
    position: { x: 740, y: 220 },
    data: {
      label: 'Notificación y Registro',
      stageKey: 'notificacion_registro',
      nodeType: 'sink',
      serviceKey: 'SRV_EMAIL_SENDER',
      badgeCount: 2,
      substages: [
        {
          id: 'sub-3',
          substage_key: 'persistencia_notif',
          title: 'Envío de Email y Guardado Final',
          is_initial: false,
          service_id: 'SRV_EMAIL_SENDER',
          service_name: 'Notificador Email',
          editor_workspace_group: 'ADMIN',
          reviewer_workspace_group: 'ADMIN',
          fields: [],
          output_fields: [],
          is_clonable: false
        }
      ]
    }
  }
];

const INITIAL_EDGES: Edge[] = [
  {
    id: 'edge-1-2',
    source: 'node-source-1',
    sourceHandle: 'out',
    target: 'node-transform-2',
    targetHandle: 'in',
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#455a64', strokeWidth: 2.2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#455a64',
      width: 16,
      height: 16
    }
  },
  {
    id: 'edge-2-3',
    source: 'node-transform-2',
    sourceHandle: 'out',
    target: 'node-sink-3',
    targetHandle: 'in',
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#455a64', strokeWidth: 2.2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#455a64',
      width: 16,
      height: 16
    }
  }
];

function StudioContent() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const { screenToFlowPosition, fitView } = useReactFlow();

  const [pipelineName, setPipelineName] = useState('Admisión y Evaluación de Crédito');
  const [pipelineDescription, setPipelineDescription] = useState('Pipeline de admisión con microservicios y validación de antecedentes');
  const [paletteCollapsed, setPaletteCollapsed] = useState(false);
  const [showMinimap, setShowMinimap] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Inspector modal state
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Connect handler
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge: Edge = {
        ...params,
        id: `edge-${Date.now()}`,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#455a64', strokeWidth: 2.2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#455a64',
          width: 16,
          height: 16
        }
      };
      setEdges((eds) => addEdge(newEdge, eds));
      showToast('Etapa conectada exitosamente');
    },
    [setEdges]
  );

  // Open configuration modal
  const handleOpenConfig = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
    setIsModalOpen(true);
  }, []);

  // Update node with config callback injected
  const nodesWithCallbacks = nodes.map(n => ({
    ...n,
    data: {
      ...n.data,
      onConfigure: handleOpenConfig
    }
  }));

  // Save changes from modal
  const handleSaveNodeConfig = (nodeId: string, updatedData: Partial<FusionNodeData>) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              ...updatedData
            }
          };
        }
        return node;
      })
    );
    showToast(`Etapa "${updatedData.label || ''}" actualizada correctamente`);
  };

  // Delete node
  const handleDeleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    showToast('Etapa eliminada del pipeline');
  };

  // Add node from Palette click or Drag&Drop
  const handleAddPaletteNode = (item: PaletteItem, position?: { x: number; y: number }) => {
    const id = `node-${Date.now()}`;
    const newPos = position || {
      x: 200 + Math.random() * 300,
      y: 150 + Math.random() * 200
    };

    const newNode: Node = {
      id,
      type: 'dataFusion',
      position: newPos,
      data: {
        label: item.name,
        stageKey: item.id.replace(/[^a-zA-Z0-9_]/g, '_'),
        nodeType: item.nodeType,
        serviceKey: item.serviceKey || 'SRV_GENERIC',
        substages: [
          {
            id: `sub_${Date.now()}`,
            substage_key: `${item.id}_sub1`,
            title: `Subetapa de ${item.name}`,
            is_initial: false,
            service_id: item.serviceKey || 'SRV_GENERIC',
            service_name: item.name,
            editor_workspace_group: 'OPERADOR',
            reviewer_workspace_group: 'ADMIN',
            fields: [
              { id: `f_${Date.now()}`, name: 'observaciones', title: 'Observaciones', type: 'string', required: false }
            ],
            output_fields: [],
            is_clonable: false
          }
        ]
      }
    };

    setNodes((nds) => [...nds, newNode]);
    showToast(`Etapa "${item.name}" agregada al lienzo`);
  };

  // Drag over canvas
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Drop on canvas
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const rawData = event.dataTransfer.getData('application/reactflow');
      if (!rawData) return;

      try {
        const item: PaletteItem = JSON.parse(rawData);
        const position = screenToFlowPosition({
          x: event.clientX,
          y: event.clientY
        });
        handleAddPaletteNode(item, position);
      } catch (err) {
        console.error('Error dropping node', err);
      }
    },
    [screenToFlowPosition]
  );

  // Quick Add stage FAB button
  const handleQuickAdd = () => {
    handleAddPaletteNode({
      id: `custom_stage_${Date.now()}`,
      name: 'Nueva Etapa',
      category: 'Transform',
      nodeType: 'transform',
      serviceKey: 'SRV_RUT_VALIDATOR',
      description: 'Etapa configurada manualmente',
      iconName: 'Wand2'
    });
  };

  // Auto layout nodes horizontally
  const handleAutoLayout = () => {
    setNodes((nds) =>
      nds.map((n, idx) => ({
        ...n,
        position: {
          x: 120 + idx * 300,
          y: 200 + (idx % 2 === 0 ? 0 : 50)
        }
      }))
    );
    setTimeout(() => fitView({ padding: 0.25, duration: 400 }), 50);
    showToast('Nodos organizados automáticamente');
  };

  // Save Pipeline JSON to Local Storage & download
  const handleSave = () => {
    const configPayload = {
      pipelineName,
      pipelineDescription,
      version: '1.0.0',
      updatedAt: new Date().toISOString(),
      nodes: nodes.map(n => ({ id: n.id, position: n.position, data: n.data })),
      edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle }))
    };
    localStorage.setItem('workflow_pipeline_studio', JSON.stringify(configPayload));
    showToast('✓ Flujo guardado correctamente');
  };

  const handleDeploy = () => {
    handleSave();
    showToast('🚀 Flujo publicado exitosamente');
  };

  const handleExport = () => {
    const configPayload = {
      name: pipelineName,
      description: pipelineDescription,
      nodes,
      edges
    };
    const blob = new Blob([JSON.stringify(configPayload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${pipelineName.toLowerCase().replace(/\s+/g, '_')}_studio.json`;
    link.click();
    showToast('Archivo JSON exportado');
  };

  const selectedNode = nodes.find(n => n.id === selectedNodeId);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#f8f9fa]">
      {/* 1. Single Clean Process Toolbar */}
      <PipelineToolbar
        pipelineName={pipelineName}
        pipelineDescription={pipelineDescription}
        onNameChange={setPipelineName}
        onDescriptionChange={setPipelineDescription}
        onSave={handleSave}
        onDeploy={handleDeploy}
        onExport={handleExport}
        onQuickAdd={handleQuickAdd}
        onAutoLayout={handleAutoLayout}
      />

      {/* 3. Main Workspace: Left Palette + Studio Canvas */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left Palette with Accordions and Service Grid */}
        <PaletteSidebar
          onAddNode={(item) => handleAddPaletteNode(item)}
          collapsed={paletteCollapsed}
          onToggleCollapse={() => setPaletteCollapsed(!paletteCollapsed)}
        />

        {/* Studio Canvas Area */}
        <div ref={reactFlowWrapper} className="flex-1 h-full relative">
          <ReactFlow
            nodes={nodesWithCallbacks}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => handleOpenConfig(node.id)}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            fitView
            defaultEdgeOptions={{
              type: 'smoothstep',
              animated: true
            }}
            proOptions={{ hideAttribution: true }}
          >
            {/* Technical Dot Grid identical to Cloud Data Fusion */}
            <Background
              variant={BackgroundVariant.Dots}
              gap={18}
              size={1.2}
              color="#cfd8dc"
              className="bg-[#fafbfc]"
            />

            {showMinimap && (
              <MiniMap
                nodeColor={(n) => {
                  const data = n.data as unknown as FusionNodeData;
                  if (data.nodeType === 'source') return '#34a853';
                  if (data.nodeType === 'sink') return '#7e57c2';
                  return '#1a73e8';
                }}
                className="!bottom-4 !left-4 !bg-white !border !border-gray-300 !rounded !shadow-md"
              />
            )}
          </ReactFlow>

          {/* Floating Controls */}
          <FloatingControls
            showMinimap={showMinimap}
            onToggleMinimap={() => setShowMinimap(!showMinimap)}
          />
        </div>
      </div>

      {/* 4. Substage & Stage Configuration Modal */}
      <StageConfigModal
        nodeId={selectedNodeId}
        initialData={selectedNode ? (selectedNode.data as unknown as FusionNodeData) : null}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveNodeConfig}
        onDeleteNode={handleDeleteNode}
      />

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-gray-900/95 text-white px-4 py-2.5 rounded-lg shadow-xl text-xs font-medium flex items-center space-x-2 animate-fade-in border border-gray-700">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <StudioContent />
    </ReactFlowProvider>
  );
}
