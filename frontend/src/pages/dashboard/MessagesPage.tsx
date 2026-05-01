import { useLocation } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';
import { useMessaging } from '@/features/messaging/model/useMessaging';
import { ChatList } from '@/features/messaging/ui/ChatList';
import { ChatView } from '@/features/messaging/ui/ChatView';

function SelectChatPlaceholder() {
  return (
    <div className='flex flex-1 flex-col items-center justify-center gap-3 px-8 text-center'>
      <div className='bg-accent/10 flex h-16 w-16 items-center justify-center rounded-2xl'>
        <MessageCircle size={28} className='text-accent' strokeWidth={2} />
      </div>
      <div>
        <p className='text-primary text-[15px] font-medium'>Выберите чат</p>
        <p className='text-secondary mt-1 text-[13px]'>
          Выберите беседу из списка слева, чтобы начать общение
        </p>
      </div>
    </div>
  );
}

export function MessagesPage() {
  const location = useLocation();
  const initialChatId = (location.state as { chatId?: string } | null)?.chatId ?? null;

  const {
    chats,
    selectedChatId,
    setSelectedChatId,
    selectedChat,
    messages,
    input,
    search,
    setSearch,
    isLoadingChats,
    isLoadingMessages,
    isSending,
    typingNames,
    keycloakId,
    messagesEndRef,
    inputRef,
    isOtherUserOnline,
    handleInputChange,
    handleSend,
    handleKeyDown,
  } = useMessaging(initialChatId);

  return (
    <div className='flex flex-1 overflow-hidden'>
      <ChatList
        chats={chats}
        selectedChatId={selectedChatId}
        search={search}
        isLoading={isLoadingChats}
        onSearch={setSearch}
        onSelect={setSelectedChatId}
      />

      {selectedChat ? (
        <ChatView
          chat={selectedChat}
          messages={messages}
          isLoading={isLoadingMessages}
          input={input}
          isSending={isSending}
          typingNames={typingNames}
          keycloakId={keycloakId}
          online={isOtherUserOnline}
          onInputChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onSend={handleSend}
          messagesEndRef={messagesEndRef}
          inputRef={inputRef}
        />
      ) : (
        <SelectChatPlaceholder />
      )}
    </div>
  );
}
