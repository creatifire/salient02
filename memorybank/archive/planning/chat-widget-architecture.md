<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Chat Widget Architecture

## Problem Statement

Multiple agent types with different UI needs:
- **Legacy Agent**: HTMX-based chat interface
- **Simple Chat Agent**: Basic text input/output
- **Sales Agent**: Lead capture, product displays, CRM integration
- **Support Agent**: Ticket creation, escalation, knowledge base search
- **Research Agent**: Document displays, citation management, workflow controls

**Requirements**: 90% code reuse, multiple deployment options, legacy compatibility, session management across agent types.

## Technical Architecture

**Preact-First Hybrid Universal Widget System:**

```typescript
// Core Foundation (90% reuse) - Built with Preact
SalientCore {
  ChatEngine,      // Message handling, session management
  AgentClient,     // Backend communication  
  StateManager,    // Preact signals/hooks for state
  ThemeSystem,     // CSS variables, styling
  A11yManager      // Accessibility, keyboard navigation
}

// Framework Adapters (5% per deployment type)
PreactAdapter extends SalientCore     // Native Preact components (primary)
ShadowDOMAdapter extends SalientCore  // Universal embedding
ReactAdapter extends SalientCore      // React compatibility via @preact/compat
VueAdapter extends SalientCore        // Vue 3 composition wrapper
IframeAdapter extends SalientCore     // Sandboxed embedding

// Agent Specializations (5% per agent type)
SimpleChatAgent extends SalientCore
SalesAgent extends SalientCore + LeadCapture + CRMIntegration  
SupportAgent extends SalientCore + TicketSystem + KnowledgeBase
ResearchAgent extends SalientCore + DocumentViewer + Citations
```

**Component Structure:**
```typescript
interface AgentWidget {
  agentType: 'legacy' | 'simple-chat' | 'sales' | 'support' | 'research';
  deployment: 'preact' | 'shadow-dom' | 'react' | 'vue' | 'iframe';
  specializations?: PreactComponent[];
  configuration: AgentConfig;
}
```

**Deployment Options:**
- **Preact Islands**: Native Astro integration (`<SalientWidget client:load />`)
- **Shadow DOM**: Universal embedding (`<script src="cdn.salient.ai/widget.js">`)
- **React/Vue**: Framework adapters via compatibility layers
- **Iframe**: Sandboxed embedding for legacy systems
- **API-Only**: Headless for mobile apps

**Backend Integration:**
- Legacy: `/chat`, `/events/stream`, `/`
- New agents: `/agents/simple-chat/`, `/agents/sales/`
- Session bridging between legacy and enhanced agents
- Configuration-driven via agent YAML configs

## Implementation Phases

**Priority 3: Preact Widget Foundation** ([0000-approach-milestone-01.md](../project-management/0000-approach-milestone-01.md))
- Preact Islands: Native Astro + Preact chat widgets
- Shadow DOM Fallback: Universal embedding for non-Preact sites  
- Simple Chat Agent: Prove 90% reuse + 10% specialization model

**Priority 4: React Compatibility**
- Preact/Compat Layer: Enable React ecosystem integration
- Component Library: NPM packages for different frameworks

**Priority 5+: Agent Specializations** ([0000-approach-milestone-01.md](../project-management/0000-approach-milestone-01.md))
- Sales Agent: First specialized agent with Preact-based UI extensions
- Support/Research Agents: Scale the pattern to additional agent types

**Legacy Support** (Parallel to all phases)
- Maintain HTMX-based functionality via `legacy.enabled` toggle
- Session bridging between legacy and enhanced agents

**Distribution Strategy:**
```bash
# NPM Packages
npm install @salient/widget-preact       # Native Preact components
npm install @salient/widget-react        # React compatibility

# Astro Integration (Primary)
<SalientWidget agent="sales" client:load />

# Shadow DOM (Universal)
<script src="cdn.salient.ai/widget/1.0/salient.js" data-agent="sales">
```
