"""Self-improver application -- handlers."""
from __future__ import annotations

from src.performance.domain.repositories import IProposalRepository, ITradeHistoryRepository
from personal.self_improver.domain.services import ImprovementAdvisorService
from personal.self_improver.domain.value_objects import WeightProposal
from personal.self_improver.infrastructure.walk_forward_adapter import WalkForwardAdapter


class GenerateProposalHandler:
    """Generates scoring weight adjustment proposals.

    Guards:
    - Returns [] if fewer than MINIMUM_TRADES closed trades
    - Runs walk-forward validation before generating proposals
    - Only proposes scoring axis weight changes (fundamental/technical/sentiment)
    - Does NOT auto-apply proposals (saves as "pending")
    """

    MINIMUM_TRADES = 50

    def __init__(
        self,
        trade_repo: ITradeHistoryRepository,
        proposal_repo: IProposalRepository,
        advisor: ImprovementAdvisorService,
        walk_forward_adapter: WalkForwardAdapter,
    ) -> None:
        self._trade_repo = trade_repo
        self._proposal_repo = proposal_repo
        self._advisor = advisor
        self._wf_adapter = walk_forward_adapter

    def handle(self) -> list[WeightProposal]:
        """Generate proposals if enough trades exist.

        Returns:
            List of WeightProposal saved to proposal_repo, or [] if < 50 trades.
        """
        count = self._trade_repo.count()
        if count < self.MINIMUM_TRADES:
            return []

        trades = self._trade_repo.find_all()
        trade_returns = [t.pnl_pct for t in trades]

        # Walk-forward validation must run before generating proposals
        wf_result = self._wf_adapter.run(trade_returns)

        # Read current weights (read-only)
        from src.scoring.domain.services import REGIME_SCORING_WEIGHTS

        proposals = self._advisor.suggest(wf_result, REGIME_SCORING_WEIGHTS)

        # Save proposals (status = "pending", no auto-apply)
        for p in proposals:
            self._proposal_repo.save({
                "id": p.id,
                "regime": p.regime,
                "axis": p.axis,
                "current_weight": p.current_weight,
                "proposed_weight": p.proposed_weight,
                "walk_forward_sharpe": p.walk_forward_sharpe,
                "status": p.status,
            })

        return proposals
