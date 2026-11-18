import React from 'react';
import { ChatPanel, ChatPanelProps } from './ChatPanel';

export const ChatCoPilot: React.FC<ChatPanelProps> = (props) => {
  return <ChatPanel {...props} />;
};

export { ChatPanel };
export default ChatCoPilot;
