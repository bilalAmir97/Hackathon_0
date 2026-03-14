"""Mock WhatsApp Web page fixtures for testing.

Provides mock DOM elements that simulate WhatsApp Web structure for testing
the WhatsApp Watcher without requiring actual browser automation.
"""

from typing import List, Dict, Any


class MockWhatsAppElement:
    """Mock DOM element for WhatsApp Web testing."""

    def __init__(self, tag: str, attributes: Dict[str, str] = None, text: str = ""):
        self.tag = tag
        self.attributes = attributes or {}
        self.text = text
        self.children: List['MockWhatsAppElement'] = []

    def query_selector(self, selector: str) -> 'MockWhatsAppElement':
        """Mock querySelector implementation."""
        # Simple selector matching for data-testid
        if selector.startswith('[data-testid="'):
            testid = selector.split('"')[1]
            return self._find_by_testid(testid)
        return None

    def query_selector_all(self, selector: str) -> List['MockWhatsAppElement']:
        """Mock querySelectorAll implementation."""
        results = []
        if selector.startswith('[data-testid="'):
            testid = selector.split('"')[1]
            self._find_all_by_testid(testid, results)
        return results

    def _find_by_testid(self, testid: str) -> 'MockWhatsAppElement':
        """Find first element with matching data-testid."""
        if self.attributes.get('data-testid') == testid:
            return self
        for child in self.children:
            result = child._find_by_testid(testid)
            if result:
                return result
        return None

    def _find_all_by_testid(self, testid: str, results: List['MockWhatsAppElement']):
        """Find all elements with matching data-testid."""
        if self.attributes.get('data-testid') == testid:
            results.append(self)
        for child in self.children:
            child._find_all_by_testid(testid, results)


def create_mock_chat_element(sender: str, message: str, timestamp: str, unread: bool = True) -> MockWhatsAppElement:
    """Create a mock chat list item element.

    Args:
        sender: Contact or group name
        message: Message preview text
        timestamp: Display timestamp (e.g., "10:30 AM")
        unread: Whether chat has unread messages

    Returns:
        MockWhatsAppElement representing a chat item
    """
    chat = MockWhatsAppElement('div', {'data-testid': 'chat-item', 'class': 'chat-item'})

    # Sender name element
    sender_elem = MockWhatsAppElement('span', {'data-testid': 'chat-sender'}, sender)
    chat.children.append(sender_elem)

    # Message preview element
    message_elem = MockWhatsAppElement('span', {'data-testid': 'chat-message'}, message)
    chat.children.append(message_elem)

    # Timestamp element
    time_elem = MockWhatsAppElement('span', {'data-testid': 'chat-timestamp'}, timestamp)
    chat.children.append(time_elem)

    # Unread indicator
    if unread:
        unread_elem = MockWhatsAppElement('span', {'data-testid': 'unread-indicator', 'class': 'unread'})
        chat.children.append(unread_elem)

    return chat


def create_mock_whatsapp_page(chats: List[Dict[str, Any]] = None) -> MockWhatsAppElement:
    """Create a complete mock WhatsApp Web page structure.

    Args:
        chats: List of chat dictionaries with keys: sender, message, timestamp, unread

    Returns:
        MockWhatsAppElement representing the full page
    """
    page = MockWhatsAppElement('html')

    # Chat list container
    chat_list = MockWhatsAppElement('div', {'data-testid': 'chat-list', 'class': 'chat-list-container'})

    # Add chat items
    if chats:
        for chat_data in chats:
            chat_elem = create_mock_chat_element(
                sender=chat_data.get('sender', 'Unknown'),
                message=chat_data.get('message', ''),
                timestamp=chat_data.get('timestamp', ''),
                unread=chat_data.get('unread', True)
            )
            chat_list.children.append(chat_elem)

    page.children.append(chat_list)
    return page


def create_mock_qr_code_page() -> MockWhatsAppElement:
    """Create a mock WhatsApp Web page showing QR code (not logged in).

    Returns:
        MockWhatsAppElement representing QR code screen
    """
    page = MockWhatsAppElement('html')
    qr_container = MockWhatsAppElement('div', {'data-testid': 'qr-code', 'class': 'qr-code-container'})
    qr_canvas = MockWhatsAppElement('canvas', {'data-testid': 'qr-canvas'})
    qr_container.children.append(qr_canvas)
    page.children.append(qr_container)
    return page


def create_mock_logged_in_page() -> MockWhatsAppElement:
    """Create a mock WhatsApp Web page showing logged in state.

    Returns:
        MockWhatsAppElement representing logged in screen with empty chat list
    """
    return create_mock_whatsapp_page(chats=[])


# Sample test data
SAMPLE_PRIORITY_CHATS = [
    {
        'sender': 'John Doe',
        'message': 'URGENT: Need the invoice for last month',
        'timestamp': '10:30 AM',
        'unread': True
    },
    {
        'sender': 'Jane Smith',
        'message': 'IMPORTANT: Meeting rescheduled to tomorrow',
        'timestamp': '11:15 AM',
        'unread': True
    },
    {
        'sender': 'Bob Wilson',
        'message': 'Help needed with project deadline',
        'timestamp': 'Yesterday',
        'unread': True
    }
]

SAMPLE_NON_PRIORITY_CHATS = [
    {
        'sender': 'Alice Brown',
        'message': 'Thanks for the update!',
        'timestamp': '9:00 AM',
        'unread': True
    },
    {
        'sender': 'Charlie Davis',
        'message': 'See you later',
        'timestamp': '8:45 AM',
        'unread': True
    }
]
