"""
BioContext MCP Integration for ARP v24

Integrates BioContext MCP servers for enhanced biological data access.
Based on: https://github.com/BioContext

Usage:
    from biocontext_mcp import BioContextIntegration
    
    # Initialize integration
    biocontext = BioContextIntegration()
    
    # Query compound data
    compound_info = biocontext.query_pubchem("aspirin")
    
    # Get target information
    target_info = biocontext.query_uniprot("P00746")  # Factor Xa
    
    # Search bioactivities
    activities = biocontext.query_chembl("CHEMBL25", target="CHEMBL1862")
"""

import json
import subprocess
import os
from typing import Dict, List, Optional, Any
import requests

class BioContextIntegration:
    """Integration layer for BioContext MCP servers"""
    
    def __init__(self, config_path: str = None):
        """Initialize BioContext integration"""
        self.config = self._load_config(config_path)
        self.mcp_servers = {
            'pubchem': {
                'command': 'python',
                'args': ['-m', 'mcp_server'],
                'port': 8001
            },
            'chembl': {
                'command': 'python', 
                'args': ['-m', 'mcp_server'],
                'port': 8002
            },
            'uniprot': {
                'command': 'python',
                'args': ['-m', 'mcp_server'],
                'port': 8003
            }
        }
        
    def _load_config(self, config_path: str = None):
        """Load MCP server configuration"""
        default_config = {
            'servers': {
                'pubchem': {
                    'url': 'http://localhost:8001',
                    'tools': ['search_compound', 'get_compound_details', 'get_compound_properties']
                },
                'chembl': {
                    'url': 'http://localhost:8002',
                    'tools': ['search_molecule', 'get_molecule_details', 'get_bioactivities']
                },
                'uniprot': {
                    'url': 'http://localhost:8003',
                    'tools': ['search_protein', 'get_protein_details']
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    def _make_mcp_request(self, server: str, tool: str, params: Dict[str, Any] = None):
        """Make request to MCP server"""
        server_config = self.config['servers'].get(server)
        if not server_config:
            raise ValueError(f"Server {server} not configured")
        
        # For now, use direct API calls as fallback
        # In production, would use actual MCP client
        return self._api_fallback(server, tool, params)
    
    def _api_fallback(self, server: str, tool: str, params: Dict[str, Any] = None):
        """API fallback for testing (replace with actual MCP calls)"""
        if server == 'pubchem':
            return self._pubchem_api(tool, params)
        elif server == 'chembl':
            return self._chembl_api(tool, params)
        elif server == 'uniprot':
            return self._uniprot_api(tool, params)
        else:
            raise ValueError(f"Unknown server: {server}")
    
    def _pubchem_api(self, tool: str, params: Dict[str, Any] = None):
        """PubChem API wrapper"""
        base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        
        if tool == 'search_compound':
            name = params.get('name', '')
            url = f"{base_url}/compound/name/{name}/JSON"
            response = requests.get(url)
            return response.json()
            
        elif tool == 'get_compound_details':
            cid = params.get('cid', '')
            url = f"{base_url}/compound/CID/{cid}/JSON"
            response = requests.get(url)
            return response.json()
            
        return {}
    
    def _chembl_api(self, tool: str, params: Dict[str, Any] = None):
        """ChEMBL API wrapper"""
        base_url = "https://www.ebi.ac.uk/chembl/api/data"
        
        if tool == 'search_molecule':
            query = params.get('query', '')
            url = f"{base_url}/molecule?molecule_chembl_id__icontains={query}"
            response = requests.get(url)
            return response.json()
            
        elif tool == 'get_bioactivities':
            chembl_id = params.get('chembl_id', '')
            url = f"{base_url}/compound_activity/compound__molecule_chembl_id/{chembl_id}"
            response = requests.get(url)
            return response.json()
            
        return {}
    
    def _uniprot_api(self, tool: str, params: Dict[str, Any] = None):
        """UniProt API wrapper"""
        base_url = "https://www.uniprot.org/uniprot"
        
        if tool == 'search_protein':
            query = params.get('query', '')
            url = f"{base_url}/?query={query}&format=json"
            response = requests.get(url)
            return response.json()
            
        elif tool == 'get_protein_details':
            uniprot_id = params.get('uniprot_id', '')
            url = f"{base_url}/{uniprot_id}.json"
            response = requests.get(url)
            return response.json()
            
        return {}
    
    # High-level ARP integration methods
    def validate_target(self, target_id: str, target_type: str = 'gene'):
        """Validate target using UniProt and OpenTargets"""
        results = {}
        
        # Get UniProt information
        if target_type == 'protein':
            uni_data = self._make_mcp_request('uniprot', 'get_protein_details', 
                                           {'uniprot_id': target_id})
            results['uniprot'] = uni_data
        
        # Get target evidence from OpenTargets (if available)
        # results['opentargets'] = self._make_mcp_request('opentargets', 'get_target_evidence',
        #                                               {'target_id': target_id})
        
        return results
    
    def screen_compounds(self, target_id: str, compound_list: List[str] = None):
        """Screen compounds against target"""
        results = {}
        
        if compound_list:
            for compound in compound_list:
                # Get compound properties from PubChem
                pubchem_data = self._make_mcp_request('pubchem', 'search_compound',
                                                    {'name': compound})
                results[compound] = {'pubchem': pubchem_data}
                
                # Get bioactivities from ChEMBL
                chembl_data = self._make_mcp_request('chembl', 'get_bioactivities',
                                                    {'chembl_id': 'CHEMBL25'})
                results[compound]['chembl'] = chembl_data
        
        return results
    
    def get_compound_properties(self, compound_name: str):
        """Get comprehensive compound properties"""
        # PubChem properties
        pubchem_data = self._make_mcp_request('pubchem', 'get_compound_details',
                                            {'name': compound_name})
        
        # ChEMBL activities
        chembl_data = self._make_mcp_request('chembl', 'search_molecule',
                                            {'query': compound_name})
        
        return {
            'pubchem': pubchem_data,
            'chembl': chembl_data
        }
    
    def literature_search(self, query: str, limit: int = 10):
        """Search PubMed for relevant literature"""
        # PubMed MCP integration
        return self._make_mcp_request('pubmed', 'search', 
                                    {'query': query, 'limit': limit})

# Example usage for ARP pipeline
def arp_biocontext_example():
    """Example of using BioContext in ARP pipeline"""
    
    biocontext = BioContextIntegration()
    
    # Example 1: Validate a target
    target_validation = biocontext.validate_target("P00746", "protein")  # Factor Xa
    print(f"Target validation: {target_validation}")
    
    # Example 2: Screen compounds
    candidates = ["aspirin", "ibuprofen", "warfarin"]
    screening_results = biocontext.screen_compounds("P00746", candidates)
    print(f"Screening results: {screening_results}")
    
    # Example 3: Get compound properties
    properties = biocontext.get_compound_properties("resveratrol")
    print(f"Compound properties: {properties}")
    
    return {
        'target_validation': target_validation,
        'screening_results': screening_results,
        'compound_properties': properties
    }

if __name__ == "__main__":
    # Test the integration
    results = arp_biocontext_example()
    print("BioContext Integration Results:")
    print(json.dumps(results, indent=2, default=str))
