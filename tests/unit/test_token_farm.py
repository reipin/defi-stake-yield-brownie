from brownie import network, exceptions
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIROMENTS,
    INITIAL_PRICE_FEED_VALUE,
    get_account,
    get_contract,
)
from scripts.deploy import deploy_dapp_token_and_token_farm
import pytest


def test_set_pricefeed_contract():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, dapp_token = deploy_dapp_token_and_token_farm()
    # Act
    token = dapp_token.address
    priceFeed = get_contract("dai_usd_price_feed")
    token_farm.setPriceFeedContract(token, priceFeed, {"from": account})

    # Assert
    assert token_farm.tokenPriceFeedMapping(token) == priceFeed
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.setPriceFeedContract(token, priceFeed, {"from": non_owner})


# amount_staked declered at tests/conftest.py
def test_stake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, dapp_token = deploy_dapp_token_and_token_farm()
    # Act
    dapp_token.approve(token_farm.address, amount_staked, {"from": account})
    token_farm.stakeTokens(dapp_token, amount_staked, {"from": account})
    # Assert
    # To get a value from solidity mapping inside mapping, use Mapping(type, type,...)
    assert (
        token_farm.stakingBalance(dapp_token.address, account.address) == amount_staked
    )
    assert token_farm.uniqueTokensStaked(account.address) == 1
    assert token_farm.stakers(0) == account.address
    return token_farm, dapp_token


def test_issue_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, dapp_token = test_stake_tokens(amount_staked)
    inicial_balance = dapp_token.balanceOf(account.address)
    # Act
    token_farm.issueToken({"from": account})
    # Assert
    assert (
        dapp_token.balanceOf(account.address)
        == inicial_balance + INITIAL_PRICE_FEED_VALUE
    )
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.issueToken({"from": non_owner})


def test_unstake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token_farm, dapp_token = test_stake_tokens(amount_staked)
    inicial_balance = dapp_token.balanceOf(account.address)
    # Act
    token_farm.unstakeTokens(dapp_token.address, {"from": account})
    # Assert
    assert dapp_token.balanceOf(account.address) == inicial_balance + amount_staked
    assert token_farm.stakingBalance(dapp_token.address, account.address) == 0
    assert token_farm.uniqueTokensStaked(account.address) == 0
