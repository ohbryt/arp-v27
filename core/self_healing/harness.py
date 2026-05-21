"""
ARP v25 - Self-Healing Harness
Based on Peter Pang's Self-Healing Agent Harness

NEW in v25: Autonomous error recovery and self-correction
Reference: Peter Pang et al. "A Self-Healing Agent Harness for Scientific Discovery"
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of errors that can occur"""
    UNKNOWN = "unknown"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    AUTH_ERROR = "auth_error"

@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    error_type: ErrorType
    message: str
    timestamp: str
    stack_trace: str
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False

@dataclass
class HealingStrategy:
    """A strategy for recovering from an error"""
    error_type: ErrorType
    strategy_name: str
    handler: Callable
    max_retries: int = 3

class SelfHealingHarness:
    """
    Self-healing harness that catches, diagnoses, and recovers from errors.
    Implements the Peter Pang framework for autonomous error recovery.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.error_log: List[ErrorRecord] = []
        self.strategies: Dict[ErrorType, List[HealingStrategy]] = {}
        self.metrics: Dict[str, int] = {
            "total_calls": 0,
            "successful": 0,
            "healed": 0,
            "failed": 0,
        }
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default healing strategies"""
        
        # API Error strategy - retry with exponential backoff
        self.register_strategy(HealingStrategy(
            error_type=ErrorType.API_ERROR,
            strategy_name="exponential_backoff",
            handler=self._handle_api_error,
            max_retries=3
        ))
        
        # Timeout strategy - retry with longer timeout
        self.register_strategy(HealingStrategy(
            error_type=ErrorType.TIMEOUT,
            strategy_name="timeout_retry",
            handler=self._handle_timeout,
            max_retries=2
        ))
        
        # Rate limit strategy - wait and retry
        self.register_strategy(HealingStrategy(
            error_type=ErrorType.RATE_LIMIT,
            strategy_name="rate_limit_wait",
            handler=self._handle_rate_limit,
            max_retries=5
        ))
        
        # Validation error - try to fix input
        self.register_strategy(HealingStrategy(
            error_type=ErrorType.VALIDATION_ERROR,
            strategy_name="input_fix",
            handler=self._handle_validation_error,
            max_retries=1
        ))
        
        # Network error - retry
        self.register_strategy(HealingStrategy(
            error_type=ErrorType.NETWORK_ERROR,
            strategy_name="network_retry",
            handler=self._handle_network_error,
            max_retries=3
        ))
        
        # Parsing error - try alternative parsing
        self.register_strategy(HealingStrategy(
            error_type=ErrorType.PARSING_ERROR,
            strategy_name="alt_parsing",
            handler=self._handle_parsing_error,
            max_retries=2
        ))
    
    def register_strategy(self, strategy: HealingStrategy):
        """Register a healing strategy for an error type"""
        if strategy.error_type not in self.strategies:
            self.strategies[strategy.error_type] = []
        self.strategies[strategy.error_type].append(strategy)
    
    async def run(
        self,
        func: Callable,
        *args,
        context: Optional[Dict] = None,
        max_total_retries: int = 5,
        **kwargs
    ) -> Any:
        """
        Run a function with self-healing capabilities.
        
        Args:
            func: Function to run
            *args: Function arguments
            context: Additional context for error handling
            max_total_retries: Maximum total retry attempts
            **kwargs: Function keyword arguments
        
        Returns:
            Function result if successful
        
        Raises:
            Exception: If all healing attempts fail
        """
        context = context or {}
        total_retries = 0
        
        while total_retries <= max_total_retries:
            try:
                self.metrics["total_calls"] += 1
                result = await func(*args, **kwargs)
                self.metrics["successful"] += 1
                return result
                
            except Exception as e:
                error_record = self._create_error_record(e, context)
                error_type = self._classify_error(e)
                
                logger.warning(f"Error occurred: {error_type.value} - {str(e)}")
                
                # Try to heal
                healed = await self._attempt_healing(
                    error_record,
                    error_type,
                    func,
                    args,
                    kwargs,
                    total_retries
                )
                
                if healed:
                    total_retries += 1
                    self.metrics["healed"] += 1
                    continue
                else:
                    self.metrics["failed"] += 1
                    self.error_log.append(error_record)
                    raise
        
        self.metrics["failed"] += 1
        raise Exception(f"Failed after {max_total_retries} healing attempts")
    
    def _create_error_record(self, error: Exception, context: Dict) -> ErrorRecord:
        """Create an error record"""
        import uuid
        return ErrorRecord(
            error_id=f"err_{uuid.uuid4().hex[:8]}",
            error_type=ErrorType.UNKNOWN,
            message=str(error),
            timestamp=datetime.now().isoformat(),
            stack_trace=traceback.format_exc(),
            context=context
        )
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify an error into an ErrorType"""
        error_str = str(error).lower()
        
        if "api" in error_str or "request" in error_str:
            return ErrorType.API_ERROR
        elif "timeout" in error_str or "timed out" in error_str:
            return ErrorType.TIMEOUT
        elif "rate limit" in error_str or "429" in error_str:
            return ErrorType.RATE_LIMIT
        elif "validation" in error_str or "invalid" in error_str:
            return ErrorType.VALIDATION_ERROR
        elif "network" in error_str or "connection" in error_str:
            return ErrorType.NETWORK_ERROR
        elif "parse" in error_str or "json" in error_str:
            return ErrorType.PARSING_ERROR
        elif "auth" in error_str or "401" in error_str or "403" in error_str:
            return ErrorType.AUTH_ERROR
        else:
            return ErrorType.UNKNOWN
    
    async def _attempt_healing(
        self,
        error_record: ErrorRecord,
        error_type: ErrorType,
        func: Callable,
        args: tuple,
        kwargs: dict,
        current_retries: int
    ) -> bool:
        """Attempt to heal an error"""
        strategies = self.strategies.get(error_type, [])
        
        for strategy in strategies:
            if current_retries >= strategy.max_retries:
                continue
            
            try:
                logger.info(f"Attempting healing strategy: {strategy.strategy_name}")
                
                # Execute strategy handler
                new_args, new_kwargs = await strategy.handler(
                    error_record,
                    args,
                    kwargs,
                    current_retries
                )
                
                # Retry with new parameters
                result = await func(*new_args, **new_kwargs)
                error_record.recovery_attempted = True
                error_record.recovery_successful = True
                return True
                
            except Exception as healing_error:
                logger.warning(f"Healing strategy failed: {str(healing_error)}")
                continue
        
        return False
    
    # Default healing handlers
    async def _handle_api_error(
        self,
        error: ErrorRecord,
        args: tuple,
        kwargs: dict,
        retries: int
    ) -> tuple:
        """Handle API errors with exponential backoff"""
        import asyncio
        wait_time = 2 ** retries  # Exponential backoff
        await asyncio.sleep(wait_time)
        return args, kwargs
    
    async def _handle_timeout(
        self,
        error: ErrorRecord,
        args: tuple,
        kwargs: dict,
        retries: int
    ) -> tuple:
        """Handle timeout by increasing timeout"""
        if "timeout" not in kwargs:
            kwargs["timeout"] = 60  # Default 60s
        else:
            kwargs["timeout"] *= 2  # Double timeout
        return args, kwargs
    
    async def _handle_rate_limit(
        self,
        error: ErrorRecord,
        args: tuple,
        kwargs: dict,
        retries: int
    ) -> tuple:
        """Handle rate limits by waiting"""
        import asyncio
        wait_time = (retries + 1) * 10  # 10s, 20s, 30s...
        await asyncio.sleep(wait_time)
        return args, kwargs
    
    async def _handle_validation_error(
        self,
        error: ErrorRecord,
        args: tuple,
        kwargs: dict,
        retries: int
    ) -> tuple:
        """Handle validation errors by cleaning input"""
        # Try to clean/sanitize inputs
        if "input" in kwargs:
            kwargs["input"] = str(kwargs["input"]).strip()
        return args, kwargs
    
    async def _handle_network_error(
        self,
        error: ErrorRecord,
        args: tuple,
        kwargs: dict,
        retries: int
    ) -> tuple:
        """Handle network errors with retry"""
        import asyncio
        await asyncio.sleep(1)  # Brief wait
        return args, kwargs
    
    async def _handle_parsing_error(
        self,
        error: ErrorRecord,
        args: tuple,
        kwargs: dict,
        retries: int
    ) -> tuple:
        """Handle parsing errors by trying alternate parsing"""
        # Add alternative parsing flag
        kwargs["alt_parse"] = True
        return args, kwargs
    
    def get_metrics(self) -> Dict[str, int]:
        """Get harness metrics"""
        return self.metrics.copy()
    
    def get_error_log(self) -> List[Dict]:
        """Get error log"""
        return [
            {
                "id": e.error_id,
                "type": e.error_type.value,
                "message": e.message,
                "timestamp": e.timestamp,
                "recovered": e.recovery_successful
            }
            for e in self.error_log
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on harness"""
        total = self.metrics["total_calls"]
        if total == 0:
            success_rate = 1.0
        else:
            success_rate = (self.metrics["successful"] + self.metrics["healed"]) / total
        
        return {
            "healthy": success_rate >= 0.9,
            "success_rate": success_rate,
            "metrics": self.metrics,
            "error_types": len(self.strategies),
            "recent_errors": len(self.error_log[-10:]) if self.error_log else 0
        }
