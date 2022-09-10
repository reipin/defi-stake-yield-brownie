from brownie import (
    accounts,
    network,
    config,
    Contract,
    MockV3Aggregator,
    MockWeth,
    MockDai,
)


FORKED_LOCAL_ENVIROMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIROMENTS = ["development", "ganache-local"]


def get_account(index=None, id=None):
    # account[0]
    # accounts.add("env")
    # accounts.load("id")
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENTS
        or network.show_active() in FORKED_LOCAL_ENVIROMENTS
    ):
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "dai_usd_price_feed": MockV3Aggregator,
    "weth_token": MockWeth,
    "fau_token": MockDai,
}


def get_contract(contract_name):
    """
    This function will grab the contract addresses from the brownie config
    if defiend, otherwise, it will deploy a mock version of that contract,
    and return that mock contract.

        Args (arguments) :
            contract_name (string)

        Returns:
            brownie.network.contract.ProjectContract: The most recently
            deployed version of this contract.
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        # if MockV3Aggregator is not deployed yet
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # address
        # abi
        # using "Contract.from_abi" function in brownie is a one way to interact with contract
        # Mock contract has a same structure as a real contract that we can use

        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


DECIMALS = 18
INITIAL_PRICE_FEED_VALUE = 2000000000000000000000


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_PRICE_FEED_VALUE):
    account = get_account()
    # We can check "constructor" in each contract which var to pass for deployment
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    print("MockV3Aggregator Deployed!")
    print("Deployind WETH token...")
    weth_token = MockWeth.deploy({"from": account})
    print(f"WETH token diployed at {weth_token.address}")
    print("Now deploying DAI token....")
    dai_token = MockDai.deploy({"from": account})
    print(f"Mock Dai token deployed at {dai_token.address}")
