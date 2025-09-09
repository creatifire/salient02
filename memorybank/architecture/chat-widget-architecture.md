# Chat Widget Architecture

## Problem Statement

The Salient AI system requires a UI architecture that can support multiple agent types with different capabilities while maintaining code reusability and consistent user experience. Key challenges include:

**Multiple Agent Types with Varying UI Needs:**
- **Legacy Agent**: Existing HTMX-based chat interface for backward compatibility
- **Simple Chat Agent**: Minimal UI with basic text input/output
- **Sales Agent**: Specialized forms (lead capture, product displays, CRM integration buttons)  
- **Support Agent**: Ticket creation, escalation options, knowledge base search
- **Research Agents**: Document displays, citation management, research workflow controls

**Development Efficiency vs. Specialization:**
- **Code Duplication Risk**: Each agent having completely separate widgets leads to maintenance overhead
- **User Experience Fragmentation**: Different interfaces for different agents creates learning curve
- **Technical Debt**: Divergent widget implementations becoming incompatible over time
- **Scaling Challenges**: Each new agent type requiring entirely new widget development

**Integration Requirements:**
- Session management across agent types
- Legacy compatibility during transition
- Mobile responsiveness across all agent widgets
- Consistent branding and accessibility standards

## Technical Architecture

**Component-Based Hybrid Approach:**

```typescript
// Shared Foundation Components (90% of code)
ChatContainer          // Layout, session management, responsive design
├── MessageList        // Conversation display, message types, styling  
├── InputArea          // Text input, file upload, voice input
├── TypingIndicator    // Loading states, agent typing animation
├── ErrorHandling      // Error display, retry mechanisms
└── SessionManager     // State management, persistence, authentication

// Agent-Specific Specialization Layers (10% of code)  
AgentWidgets/
├── LegacyWidget       // Existing HTMX-based interface for backward compatibility
├── SimpleChatWidget   // Minimal UI, basic text interaction
├── SalesAgentWidget   // + Lead forms, product displays, CRM buttons
├── SupportAgentWidget // + Ticket creation, escalation, knowledge search  
└── ResearchWidget     // + Document panels, citation tools, workflow controls
```

**Implementation Strategy:**
- **Shared Core**: Common chat functionality, session management, message persistence
- **Composition Pattern**: Agent widgets compose shared components with specialized additions
- **Configuration-Driven**: Agent-specific UI elements defined in YAML configuration
- **Progressive Enhancement**: Start with unified widget, add specializations as agents are developed

**Component Communication:**
```typescript
interface AgentWidget {
  agentType: 'legacy' | 'simple-chat' | 'sales' | 'support' | 'research';
  sharedComponents: ChatContainer;
  specializedComponents?: {
    inputExtensions?: React.Component[];    // Custom input fields
    toolPanels?: React.Component[];         // Agent-specific tool interfaces  
    actionButtons?: React.Component[];      // Context-specific actions
  };
  configuration: AgentConfig;
}
```

**Integration with Backend:**
- Widget architecture mirrors backend agent structure:
  - Legacy: `/chat`, `/events/stream`, `/` (existing endpoints)  
  - New agents: `/agents/simple_chat/`, `/agents/sales/` (Pydantic AI structure)
- Configuration-driven UI customization matches agent YAML configs
- Session bridging supports switching between legacy and new agent types mid-conversation
- Parallel development enabled via legacy endpoint toggle in `app.yaml`

## Implementation Phases

**Legacy Agent Support** (Parallel to all phases - [0000-approach-milestone-01.md](../project-management/0000-approach-milestone-01.md))
- **Scope**: Maintain existing HTMX-based chat functionality during transition
- **Widget Focus**: Preserve current `/chat`, `/events/stream`, `/` endpoints without changes
- **Configuration**: Toggle via `legacy.enabled` in `app.yaml` for parallel development
- **Purpose**: Enable safe testing and gradual migration without functionality loss

**Priority 2: Simple Chat Agent Implementation** (Current - [0000-approach-milestone-01.md](../project-management/0000-approach-milestone-01.md))
- **Scope**: Establish shared foundation with unified widget
- **Widget Focus**: Single widget supporting simple chat agent functionality
- **Components**: Core chat container, message display, basic input area
- **Outcome**: Solid foundation for future agent-specific customizations

**Priority 3: UI Migration to Simple Chat Agent** ([0000-approach-milestone-01.md](../project-management/0000-approach-milestone-01.md))
- **Scope**: Migrate all existing interfaces to use enhanced simple chat agent
- **Widget Impact**: 
  - Demo Page: `web/src/pages/demo/htmx-chat.astro` → enhanced agent endpoints
  - Chat Widget: `web/public/widget/chat-widget.js` → agent integration
  - HTMX Chat: `web/public/htmx-chat.html` → unified widget patterns
- **Architecture Validation**: Prove shared foundation approach works across all interface types

**Priority 5: Sales Agent Addition** ([0000-approach-milestone-01.md](../project-management/0000-approach-milestone-01.md))
- **Scope**: First specialized agent with business tools and CRM integration
- **Widget Evolution**: Add specialization layer to existing foundation
- **New Components**:
  - Lead capture forms and qualification workflows
  - Product display and recommendation interfaces
  - CRM integration buttons and contact management
- **Architecture Proof**: Validate hybrid approach with first agent-specific customization

**Future Phases**: Additional agent types (support, research) will follow the established pattern of shared foundation + agent-specific specialization layers, validating the scalability of the hybrid architecture approach.
