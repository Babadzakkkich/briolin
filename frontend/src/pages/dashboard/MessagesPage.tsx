import { useState } from 'react';
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

  const [mobilePanel, setMobilePanel] = useState<'list' | 'chat'>(
    initialChatId ? 'chat' : 'list',
  );

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
    onlineUsers,
    handleInputChange,
    handleSend,
    handleKeyDown,
    handleDeleteChat,
    handleMarkChatRead,
  } = useMessaging(initialChatId);

  const handleSelect = (id: string) => {
    setSelectedChatId(id);
    setMobilePanel('chat');
  };

  const handleBack = () => {
    setMobilePanel('list');
  };

  return (
    <div className='relative flex flex-1 overflow-hidden'>
      {/* List panel — on mobile: full-screen base layer; on desktop: fixed sidebar */}
      <div
        className={[
          'absolute inset-0 z-10 flex flex-col bg-white',
          'md:relative md:inset-auto md:z-auto md:w-72 md:shrink-0',
        ].join(' ')}
      >
        <ChatList
          chats={chats}
          selectedChatId={selectedChatId}
          search={search}
          isLoading={isLoadingChats}
          onlineUsers={onlineUsers}
          onSearch={setSearch}
          onSelect={handleSelect}
          onDeleteChat={handleDeleteChat}
          onMarkChatRead={handleMarkChatRead}
        />
      </div>

      {/* Chat panel — slides over the list on mobile; flex-1 on desktop */}
      <div
        className={[
          'absolute inset-0 z-20 flex flex-col bg-white transition-transform duration-300 ease-in-out',
          mobilePanel === 'list' ? 'translate-x-full' : 'translate-x-0',
          'md:relative md:inset-auto md:z-auto md:flex-1 md:translate-x-0',
        ].join(' ')}
      >
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
            onBack={handleBack}
            onDeleteChat={handleDeleteChat}
          />
        ) : (
          <SelectChatPlaceholder />
        )}
      </div>
    </div>
  );
}
