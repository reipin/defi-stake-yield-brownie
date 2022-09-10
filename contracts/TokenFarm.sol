//stakeToken
//unstakeToken
//issueToken
//getEthValue
//addAllowedToken
//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract TokenFarm is Ownable {
    address[] public allowedTokens;
    // mapping token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // Track to get an idea of how many token each user is staking
    mapping(address => uint256) public uniqueTokensStaked;
    // Map stakable token address to price feed address
    mapping(address => address) public tokenPriceFeedMapping;
    address[] public stakers;
    // Make dappToken as a static variable
    IERC20 public dappToken;

    // 50 ETH and 50 DAI staked, and we want to give 1 DAPP / 1 DAI.

    // We need deployed Dapp token address to send rewards => use constructor for this
    constructor(address _dappTokenAddress) public {
        dappToken = IERC20(_dappTokenAddress);
    }

    function setPriceFeedContract(address _token, address _priceFeed)
        public
        onlyOwner
    {
        tokenPriceFeedMapping[_token] = _priceFeed;
    }

    function issueToken() public onlyOwner {
        // Issue token to all staker
        for (
            uint256 stakersIndex = 0;
            stakersIndex < stakers.length;
            stakersIndex++
        ) {
            address recipient = stakers[stakersIndex];
            uint256 userTotalValue = getUserTotalValue(recipient);
            // Send DAPP rewards
            // Based on thier total locked value
            //dappToken.transfer(recipient, value);
            dappToken.transfer(recipient, userTotalValue);
        }
    }

    function getUserTotalValue(address _user) public view returns (uint256) {
        uint256 totalValue = 0;
        require(uniqueTokensStaked[_user] >= 1, "You have no token staked");
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ) {
            totalValue += getUserSingleTokenValue(
                _user,
                allowedTokens[allowedTokensIndex]
            );
        }
        return totalValue;
    }

    function getUserSingleTokenValue(address _user, address _token)
        public
        view
        returns (uint256)
    {
        if (uniqueTokensStaked[_user] <= 0) {
            return 0;
        }
        (uint256 price, uint256 decimals) = getTokenValue(_token);
        return ((stakingBalance[_token][_user] * price) / (10**decimals));
    }

    function getTokenValue(address _token)
        public
        view
        returns (uint256, uint256)
    {
        address priceFeedAddress = tokenPriceFeedMapping[_token];
        AggregatorV3Interface priceFeed;
        priceFeed = AggregatorV3Interface(priceFeedAddress);
        // Grab price
        (, int256 price, , , ) = priceFeed.latestRoundData();
        // Grab decimals to able to match all tokens
        uint256 decimals = uint256(priceFeed.decimals());
        return (uint256(price), decimals);
    }

    function stakeTokens(address _token, uint256 _amount) public payable {
        require(_amount > 0, "Amount must be grater than zero");
        require(tokenIsAllowed(_token), "Token not allowed");
        // Wrap token with IERC to use transferFrom function inside the contract.
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        stakingBalance[_token][msg.sender] += _amount;
        // Track to get an idea of how many token each user is staking
        updateUniqueTokenStaked(msg.sender, _token);
        if (uniqueTokensStaked[msg.sender] == 1) {
            stakers.push(msg.sender);
        }
    }

    function unstakeTokens(address _token) public {
        uint256 balance = stakingBalance[_token][msg.sender];
        require(balance > 0, "The staking balance cannot be zero");
        IERC20(_token).transfer(msg.sender, balance);
        stakingBalance[_token][msg.sender] = 0;
        uniqueTokensStaked[msg.sender] -= 1;
    }

    // internal function is the one only this contract can call
    function updateUniqueTokenStaked(address _user, address _token) internal {
        if (stakingBalance[_token][_user] >= 0) {
            uniqueTokensStaked[_user] += 1;
        }
    }

    function addAllowedTokens(address _token) public onlyOwner {
        allowedTokens.push(_token);
    }

    function tokenIsAllowed(address _token) public returns (bool) {
        for (
            uint256 allowedTokenIndex = 0;
            allowedTokenIndex < allowedTokens.length;
            allowedTokenIndex++
        ) {
            if (allowedTokens[allowedTokenIndex] == _token) {
                return true;
            }
        }
        return false;
    }
}
