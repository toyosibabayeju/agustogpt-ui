"""
Azure Storage Module for AgustoGPT
Handles chat persistence using Azure Blob Storage and Table Storage
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging

# Try to import Azure packages, but handle if not installed
try:
    from azure.storage.blob import BlobServiceClient, ContentSettings
    from azure.data.tables import TableServiceClient
    from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    # Create dummy classes to prevent errors
    class BlobServiceClient:
        pass
    class TableServiceClient:
        pass
    class ContentSettings:
        def __init__(self, **kwargs):
            pass
    class ResourceNotFoundError(Exception):
        pass
    class ResourceExistsError(Exception):
        pass

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureStorageManager:
    """
    Manages Azure Storage operations for chat persistence
    """
    
    def __init__(self):
        """Initialize Azure Storage clients"""
        # Check if Azure packages are available
        if not AZURE_AVAILABLE:
            logger.warning("Azure packages not installed. Storage features will be disabled. Install with: pip install azure-storage-blob azure-data-tables")
            self.enabled = False
            return
        
        # Get Azure credentials from environment
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
        self.blob_container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME', 'agustogpt-chats')
        self.table_name = os.getenv('AZURE_TABLE_NAME', 'AgustoGPTChats')
        
        if not self.connection_string:
            logger.warning("Azure Storage connection string not found. Storage features will be disabled.")
            self.enabled = False
            return
        
        self.enabled = True
        
        try:
            # Initialize Blob Service Client
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self._ensure_blob_container_exists()
            
            # Initialize Table Service Client
            self.table_service_client = TableServiceClient.from_connection_string(self.connection_string)
            self._ensure_table_exists()
            
            logger.info("Azure Storage clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Storage: {str(e)}")
            self.enabled = False
    
    def _ensure_blob_container_exists(self):
        """Create blob container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.blob_container_name)
            container_client.create_container()
            logger.info(f"Created blob container: {self.blob_container_name}")
        except ResourceExistsError:
            logger.info(f"Blob container already exists: {self.blob_container_name}")
        except Exception as e:
            logger.error(f"Error creating blob container: {str(e)}")
            raise
    
    def _ensure_table_exists(self):
        """Create table if it doesn't exist"""
        try:
            table_client = self.table_service_client.create_table_if_not_exists(self.table_name)
            logger.info(f"Table ensured: {self.table_name}")
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise
    
    def generate_chat_id(self) -> str:
        """Generate a unique chat ID"""
        return f"chat_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def save_chat_session(self, 
                         chat_id: str,
                         user_id: str,
                         messages: List[Dict[str, Any]],
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a chat session to Azure Storage
        
        Args:
            chat_id: Unique identifier for the chat
            user_id: User identifier (can be placeholder)
            messages: List of message dictionaries
            metadata: Additional metadata about the chat
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("Azure Storage is not enabled")
            return False
        
        try:
            # Prepare chat data
            chat_data = {
                'chat_id': chat_id,
                'user_id': user_id,
                'messages': messages,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'message_count': len(messages),
                'metadata': metadata or {}
            }
            
            # Save to Blob Storage (full chat log as JSON)
            blob_name = f"{user_id}/{chat_id}.json"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.blob_container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(
                data=json.dumps(chat_data, indent=2),
                content_settings=ContentSettings(content_type='application/json'),
                overwrite=True
            )
            logger.info(f"Chat saved to blob: {blob_name}")
            
            # Save metadata to Table Storage
            table_client = self.table_service_client.get_table_client(self.table_name)
            
            # Get chat title from first user message or metadata
            chat_title = "New Chat"
            if messages and len(messages) > 0:
                for msg in messages:
                    if msg.get('role') == 'user':
                        chat_title = msg.get('content', '')[:100]  # First 100 chars
                        break
            
            if metadata and 'title' in metadata:
                chat_title = metadata['title']
            
            entity = {
                'PartitionKey': user_id,
                'RowKey': chat_id,
                'ChatTitle': chat_title,
                'MessageCount': len(messages),
                'CreatedAt': chat_data['created_at'],
                'UpdatedAt': chat_data['updated_at'],
                'SearchMode': metadata.get('search_mode', 'auto') if metadata else 'auto',
                'LastMessage': messages[-1]['content'][:200] if messages else '',  # Last message preview
                'BlobPath': blob_name
            }
            
            table_client.upsert_entity(entity)
            logger.info(f"Chat metadata saved to table for chat_id: {chat_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save chat session: {str(e)}")
            return False
    
    def load_chat_session(self, chat_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a chat session from Azure Storage
        
        Args:
            chat_id: Chat identifier
            user_id: User identifier
        
        Returns:
            Dict containing chat data or None if not found
        """
        if not self.enabled:
            logger.warning("Azure Storage is not enabled")
            return None
        
        try:
            # Load from Blob Storage
            blob_name = f"{user_id}/{chat_id}.json"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.blob_container_name,
                blob=blob_name
            )
            
            blob_data = blob_client.download_blob()
            chat_data = json.loads(blob_data.readall())
            
            logger.info(f"Chat loaded from blob: {blob_name}")
            return chat_data
            
        except ResourceNotFoundError:
            logger.warning(f"Chat not found: {chat_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to load chat session: {str(e)}")
            return None
    
    def list_user_chats(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all chats for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of chats to return
        
        Returns:
            List of chat metadata dictionaries
        """
        if not self.enabled:
            logger.warning("Azure Storage is not enabled")
            return []
        
        try:
            table_client = self.table_service_client.get_table_client(self.table_name)
            
            # Query chats for the user
            query_filter = f"PartitionKey eq '{user_id}'"
            entities = table_client.query_entities(
                query_filter=query_filter,
                select=['RowKey', 'ChatTitle', 'MessageCount', 'CreatedAt', 'UpdatedAt', 'SearchMode', 'LastMessage']
            )
            
            chats = []
            count = 0
            for entity in entities:
                if count >= limit:
                    break
                    
                chats.append({
                    'chat_id': entity['RowKey'],
                    'title': entity.get('ChatTitle', 'Untitled Chat'),
                    'message_count': entity.get('MessageCount', 0),
                    'created_at': entity.get('CreatedAt', ''),
                    'updated_at': entity.get('UpdatedAt', ''),
                    'search_mode': entity.get('SearchMode', 'auto'),
                    'last_message': entity.get('LastMessage', '')
                })
                count += 1
            
            # Sort by updated_at (most recent first)
            chats.sort(key=lambda x: x['updated_at'], reverse=True)
            
            logger.info(f"Found {len(chats)} chats for user: {user_id}")
            return chats
            
        except Exception as e:
            logger.error(f"Failed to list user chats: {str(e)}")
            return []
    
    def delete_chat_session(self, chat_id: str, user_id: str) -> bool:
        """
        Delete a chat session from Azure Storage
        
        Args:
            chat_id: Chat identifier
            user_id: User identifier
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("Azure Storage is not enabled")
            return False
        
        try:
            # Delete from Blob Storage
            blob_name = f"{user_id}/{chat_id}.json"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.blob_container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_name}")
            
            # Delete from Table Storage
            table_client = self.table_service_client.get_table_client(self.table_name)
            table_client.delete_entity(partition_key=user_id, row_key=chat_id)
            logger.info(f"Deleted table entity for chat_id: {chat_id}")
            
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Chat not found for deletion: {chat_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete chat session: {str(e)}")
            return False
    
    def log_query(self,
                  chat_id: str,
                  user_id: str,
                  query: str,
                  response: str,
                  search_mode: str,
                  filters: Optional[Dict[str, Any]] = None,
                  sources: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Log a single query/response interaction
        
        Args:
            chat_id: Chat identifier
            user_id: User identifier
            query: User query
            response: System response
            search_mode: Search mode used (auto/tailored)
            filters: Applied filters
            sources: Source documents used
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("Azure Storage is not enabled")
            return False
        
        try:
            # Create log entry
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'chat_id': chat_id,
                'user_id': user_id,
                'query': query,
                'response': response,
                'search_mode': search_mode,
                'filters': filters or {},
                'sources': sources or []
            }
            
            # Save log as individual blob for analytics
            log_id = f"{datetime.now().strftime('%Y%m%d')}/{chat_id}_{datetime.now().strftime('%H%M%S')}.json"
            blob_name = f"logs/{log_id}"
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.blob_container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(
                data=json.dumps(log_entry, indent=2),
                content_settings=ContentSettings(content_type='application/json'),
                overwrite=True
            )
            
            logger.info(f"Query logged: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log query: {str(e)}")
            return False


# Create singleton instance
storage_manager = AzureStorageManager()
