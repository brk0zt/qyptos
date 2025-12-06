# -*- coding: utf-8 -*-
# memory/management/commands/test_memory.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from memory.services.advanced_memory_manager import AdvancedMemoryManager

class Command(BaseCommand):
    help = 'Test the memory system'
    
    def handle(self, *args, **options):
        user = User.objects.first()
        if not user:
            self.stdout.write('No user found')
            return
            
        memory_manager = AdvancedMemoryManager(user)
        
        # Test aramasý
        results = memory_manager.semantic_search('test document', limit=5)
        
        self.stdout.write(f"Found {len(results)} results")
        for result in results:
            self.stdout.write(
                f"- {result['file_path']} "
                f"(score: {result['similarity_score']:.2f})"
            )
