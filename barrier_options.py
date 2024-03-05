import numpy as np
import matplotlib.pyplot as plt
import sys
import argparse

class BarrierOption():
    def __init__(self, option_type, barrier_type, S0, K, B, T, volatility, risk_free_rate) -> None:
        """
        Parameters
        ----------
            option_type      (str): "call" or "put"
            barrier_type     (str): "up_and_out" or "down_and_out" or "up_and_in" or "down_and_in"
            S0             (float): initial price
            K              (float): strike price
            B              (float): barrier price
            T              (float): time to maturity in years
            volatility     (float): annual volatility of underlying
            risk_free_rate (float): annual risk free rate
        """
        if option_type != "call" and option_type != "put":
            print('Error!\nPlease make sure option_type="call" or option_type="put"')
            sys.exit()

        if barrier_type != "up_and_out" and barrier_type != "down_and_out" and barrier_type != "up_and_in" and barrier_type != "down_and_in":
            print('Error!\nPlease make sure barrier_type="up_and_out" or barrier_type="down_and_out" or barrier_type="up_and_in" or barrier_type="down_and_in"')
            sys.exit()

        if volatility < 0 or volatility > 1:
            print("Error!\nPlease make sure 0 <= volatility <= 1")
            sys.exit()
        
        self.option_type    = option_type
        self.barrier_type   = barrier_type
        self.S0             = S0
        self.K              = K
        self.B              = B
        self.T              = T
        self.volatility     = volatility
        self.risk_free_rate = risk_free_rate
    

    def contract_specification(self) -> None:
        """
        Display contract specifications
        """
        print("\nContract Specifications")
        print("-----------------------------------------------------------------------")
        print(f"Option type:                    {self.option_type}")
        print(f"Barrier type:                   {self.barrier_type}")
        print(f"Initial price:                  {self.S0}")
        print(f"Strike price:                   {self.K}")
        print(f"Barrier price:                  {self.B}")
        print(f"Time to maturity (in years):    {self.T}")
        print(f"Annual volatility:              {self.volatility}")
        print(f"Annual risk free rate:          {self.risk_free_rate}")
    

    def present_value(self, value):
        """
        Calculate the present value of future cashflows 

        Paramters
        ---------
            value (list of floats): values to be discounted 

        Returns
        --------
            pv    (list of floats): present value 
        """
        pv = np.array(value)*np.exp(-self.risk_free_rate*self.T)
        return pv


    def vanilla_payoff(self, expiration_prices):
        """
        Given the price of the underlying at maturity, calculate the payoff of the vanilla option

        Parameters
        ----------
            expiration_prices (list of floats): price of the underlying at maturity

        Returns
        ----------
            payoff            (list of floats): payoff 
        """

        if self.option_type == "call":
            payoff = np.maximum(expiration_prices - self.K, 0)
        
        #if self.option_type == "put"
        else:
            payoff = np.maximum(self.K - expiration_prices, 0)

        return payoff
    


    def contract_payoff(self, price_series):
        """
        Given the price series of a path, calculate the payoff of the barrier option

        Parameters
        ----------
            price_series   (list of floats): price series whose payoff we need to determine

        Returns
        ----------
            payoff         (list of floats): payoff of each price series
        """
        price_series = np.array(price_series)
        payoff = []
        if self.barrier_type == "up_and_out" or self.barrier_type == "up_and_in":
            max_price = np.max(price_series, axis=1) 
            barrier_reached = np.where(max_price >= self.B, 1, 0)
            if self.barrier_type == "up_and_out":
                for iter in range(len(barrier_reached)):
                    if barrier_reached[iter] == 1:
                        payoff.append(0)
                    
                    else:
                        payoff.append(self.vanilla_payoff(price_series[iter, -1]))

            #if self.barrier_type == "up_and_in"
            else:
                for iter in range(len(barrier_reached)):
                    if barrier_reached[iter] == 0:
                        payoff.append(0)
                    
                    else:
                        payoff.append(self.vanilla_payoff(price_series[iter, -1]))

        #if self.barrier_type == "down_and_out" or self.barrier_type == "down_and_in"
        else:
            min_price = np.min(price_series, axis=1)
            barrier_reached = np.where(min_price <= self.B, 1, 0)
            if self.barrier_type == "down_and_out":
                for iter in range(len(barrier_reached)):
                    if barrier_reached[iter] == 1:
                        payoff.append(0)

                    else:
                        payoff.append(self.vanilla_payoff(price_series[iter, -1]))
            
            #if self.barrier_type == "down_and_in"
            else:
                for iter in range(len(barrier_reached)):
                    if barrier_reached[iter] == 0:
                        payoff.append(0)

                    else:
                        payoff.append(self.vanilla_payoff(price_series[iter, -1]))
        
        return payoff


    def monte_carlo_pricing(self, steps, num_iters, plot=False, seed=None) -> float:
        """
        Calculate the value of the european barrier option using Monte Carlo simulations

        Parameters
        ----------
            num_iters        (int): number of montecarlo iterations
            plot            (bool): if True plot the montecarlo graph associated 
            seed             (int): select a seed for the (pseudo)random number generator
        
        Returns
        ----------
            contract_price (float): estimated price for the options contract
        """
        if seed != None:
            np.random.seed(seed)
        
        #Geometric Brownian Motion
        step_volatility = self.volatility*np.sqrt(self.T/steps) 
        Z = np.random.normal(size=(num_iters, steps)) 
        end_of_step_price = self.S0*np.cumprod(np.exp((self.risk_free_rate - 0.5*self.volatility**2)*(self.T/steps) + step_volatility*Z), axis=1)
        end_of_step_price = np.concatenate((self.S0*np.ones((num_iters,1)), end_of_step_price), axis=1)

        payoffs = self.contract_payoff(end_of_step_price)
        present_value_payoffs = self.present_value(payoffs)
        estimated_value = np.mean(present_value_payoffs)
        print(f"\nEstimated contract value: {estimated_value}")

        if plot == True:
            for iter in range(num_iters):
                plt.plot(np.linspace(0,self.T,steps + 1), end_of_step_price[iter])
             
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.axhline(self.B, color="black", linewidth=2)
            plt.text(self.T*1.05, self.B, 'Barrier', verticalalignment='center', horizontalalignment='left')
            plt.axhline(self.K, color="red", linestyle="--")
            plt.text(self.T*1.05, self.K, "Strike", verticalalignment='center', horizontalalignment='left')

            if self.barrier_type == "up_and_out":
                barrier_type = "Up & Out"
            elif self.barrier_type == "down_and_out":
                barrier_type = "Down & Out"
            elif self.barrier_type == "up_and_in":
                barrier_type = "Up & In"
            else:
                barrier_type = "Down & In"

            if self.option_type == "call":
                option_type = "Call"

            else:
                option_type = "Put"

            plt.title(f'{barrier_type} {option_type}, Strike {self.K}, Barrier {self.B}')
            plt.show()

        return estimated_value
    
def cli():
    parser = argparse.ArgumentParser(description='CLI tool to price european barrier options via Monte Carlo simulations') 

    parser.add_argument('option_type',    type=str,   help='call or put')
    parser.add_argument('barrier_type',   type=str,   help='up_and_out or down_and_out orup_and_in or down_and_in')
    parser.add_argument('S0',             type=float, help='Initial price of the underlying')
    parser.add_argument('K',              type=float, help='Strike price')
    parser.add_argument('B',              type=float, help='Barrier price')
    parser.add_argument('T',              type=float, help='Time to maturity in years')
    parser.add_argument('volatility',     type=float, help='annual volatility (between 0 and 1)')
    parser.add_argument('risk_free_rate', type=float, help='annual risk free rate')
    parser.add_argument('steps',          type=int,   help='number of steps in each simulation')
    parser.add_argument('num_iters',      type=int,   help='number of simulations')

    args = parser.parse_args()
 
    option_type    = args.option_type
    barrier_type   = args.barrier_type
    S0             = args.S0
    K              = args.K
    B              = args.B
    T              = args.T
    volatility     = args.volatility
    risk_free_rate = args.risk_free_rate
    steps          = args.steps
    num_iters      = args.num_iters

    option = BarrierOption(option_type, barrier_type, S0, K, B, T, volatility, risk_free_rate)
    option.contract_specification()
    print(f"\nNumber of steps:                {steps}")
    print(f"Number of simulations:          {num_iters}")
    option.monte_carlo_pricing(steps, num_iters, plot=True)




if __name__ == "__main__":
    cli()