import asyncio
from typing import Optional
from sqlalchemy import select, update
from app.database.session import async_session_factory
from app.database.models import BasicProfile, DetailedProfile
from app.services.embedding_service import get_embedding_service
from app.services.sentiment_service import get_sentiment_service
from app.core.logger import logger


class EmbeddingUpdater:
    """Service for updating embeddings when profile data changes"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.sentiment_service = get_sentiment_service()
    
    async def update_embedding_for_profile(self, basic_profile_id: int) -> bool:
        """
        Update both semantic and sentiment embeddings for a profile.
        
        Args:
            basic_profile_id: ID of the basic profile
        
        Returns:
            True if embedding was updated, False otherwise
        """
        try:
            async with async_session_factory() as session:
                # Get basic profile
                stmt = select(BasicProfile).where(BasicProfile.id == basic_profile_id)
                result = await session.execute(stmt)
                basic = result.scalar_one_or_none()
                
                if not basic:
                    logger.warning(f"Basic profile {basic_profile_id} not found")
                    return False
                
                # Get detailed profile
                stmt = select(DetailedProfile).where(
                    DetailedProfile.basic_profile_id == basic_profile_id
                )
                result = await session.execute(stmt)
                detailed = result.scalar_one_or_none()
                
                if not detailed:
                    logger.debug(f"No detailed profile for {basic.keycloak_id}, skipping embeddings")
                    return False
                
                # Generate semantic embedding
                semantic_embedding = await self.embedding_service.generate_profile_embedding(
                    about_me=detailed.about_me,
                    hobbies=detailed.hobbies,
                    partner_preferences=detailed.partner_preferences
                )
                
                # Generate sentiment embedding (только из about_me)
                sentiment_embedding = await self.sentiment_service.generate_sentiment_embedding(
                    detailed.about_me
                )
                
                if semantic_embedding is None and sentiment_embedding is None:
                    logger.warning(f"Failed to generate any embeddings for profile {basic_profile_id}")
                    return False
                
                # Update both embeddings
                update_values = {}
                if semantic_embedding is not None:
                    update_values["embedding"] = semantic_embedding
                if sentiment_embedding is not None:
                    update_values["sentiment_embedding"] = sentiment_embedding
                
                if update_values:
                    stmt = (
                        update(BasicProfile)
                        .where(BasicProfile.id == basic_profile_id)
                        .values(**update_values)
                    )
                    await session.execute(stmt)
                    await session.commit()
                    
                    logger.info(
                        f"Updated embeddings for user {basic.keycloak_id}: "
                        f"semantic={semantic_embedding is not None}, "
                        f"sentiment={sentiment_embedding is not None}"
                    )
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to update embeddings for profile {basic_profile_id}: {e}")
            return False
    
    async def update_embedding_on_profile_change(
        self,
        keycloak_id: str,
        about_me: Optional[str] = None,
        hobbies: Optional[str] = None,
        partner_preferences: Optional[str] = None
    ) -> bool:
        """
        Update embeddings when profile fields change.
        Called from SAGA handlers or directly.
        """
        try:
            async with async_session_factory() as session:
                # Get basic profile
                stmt = select(BasicProfile).where(BasicProfile.keycloak_id == keycloak_id)
                result = await session.execute(stmt)
                basic = result.scalar_one_or_none()
                
                if not basic:
                    logger.warning(f"Profile not found for {keycloak_id}")
                    return False
                
                # Get current detailed profile
                stmt = select(DetailedProfile).where(DetailedProfile.basic_profile_id == basic.id)
                result = await session.execute(stmt)
                detailed = result.scalar_one_or_none()
                
                if not detailed:
                    logger.debug(f"No detailed profile for {keycloak_id}, skipping embeddings")
                    return False
                
                # Use provided values or existing ones
                final_about_me = about_me if about_me is not None else detailed.about_me
                final_hobbies = hobbies if hobbies is not None else detailed.hobbies
                final_partner_preferences = partner_preferences if partner_preferences is not None else detailed.partner_preferences
                
                # Generate semantic embedding
                semantic_embedding = await self.embedding_service.generate_profile_embedding(
                    about_me=final_about_me,
                    hobbies=final_hobbies,
                    partner_preferences=final_partner_preferences
                )
                
                # Generate sentiment embedding (только из about_me)
                sentiment_embedding = await self.sentiment_service.generate_sentiment_embedding(
                    final_about_me
                )
                
                if semantic_embedding is None and sentiment_embedding is None:
                    logger.warning(f"Failed to generate any embeddings for {keycloak_id}")
                    return False
                
                # Update both embeddings
                update_values = {}
                if semantic_embedding is not None:
                    update_values["embedding"] = semantic_embedding
                if sentiment_embedding is not None:
                    update_values["sentiment_embedding"] = sentiment_embedding
                
                if update_values:
                    stmt = (
                        update(BasicProfile)
                        .where(BasicProfile.keycloak_id == keycloak_id)
                        .values(**update_values)
                    )
                    await session.execute(stmt)
                    await session.commit()
                    
                    logger.info(
                        f"Updated embeddings for {keycloak_id} after profile change: "
                        f"semantic={semantic_embedding is not None}, "
                        f"sentiment={sentiment_embedding is not None}"
                    )
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to update embeddings on profile change: {e}")
            return False


# Global instance
_embedding_updater = None


def get_embedding_updater() -> EmbeddingUpdater:
    global _embedding_updater
    if _embedding_updater is None:
        _embedding_updater = EmbeddingUpdater()
    return _embedding_updater