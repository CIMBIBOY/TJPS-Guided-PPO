import numpy as np
import time
from environment.map_generator import map_to_value
from environment.global_mapper import find_path, return_path
import os
import matplotlib.pyplot as plt
import torch
from agents.ppo_agent import PPOAgent
from agents.cnn_for_ppo import CNNLSTM

def save_evaluation_image(init_arr, start, end, agent_path, a_star_path, episode, eval_folder='G2RL-Path-Planning/eval/eval_images'):
    """
    Saves an evaluation image showing the environment, start and end positions, agent's path, and optimal path.

    Args:
        init_arr (numpy.ndarray): The initial environment array (48x48).
        start (tuple): The start posityyyyyion (x, y).
        end (tuple): The end position (x, y).
        agent_path (list): List of coordinates representing the agent's path.
        a_star_path (list): List of coordinates representing the optimal path.
        episode (int): The episode number.
        eval_folder (str): The folder where evaluation images will be saved.
    """
    plt.figure(figsize=(10, 10))
    plt.imshow(init_arr, cmap='binary')

    # Plot start and end positions
    plt.plot(start[1], start[0], 'ro', markersize=10, label='Start')
    plt.plot(end[1], end[0], 'go', markersize=10, label='End')

    # Plot agent's path
    if agent_path:
        agent_path = np.array(agent_path)
        plt.plot(agent_path[:, 1], agent_path[:, 0], 'gray', linestyle=':', linewidth=2, label="Agent's Path")

    # Plot optimal path
    if a_star_path:
        a_star_path = np.array(a_star_path)
        plt.plot(a_star_path[:, 1], a_star_path[:, 0], 'blue', linestyle=':', linewidth=2, label='Optimal Path')

    plt.title(f'Episode {episode + 1} Evaluation')
    plt.legend()
    plt.grid(False)

    # Ensure the evaluation folder exists
    os.makedirs(eval_folder, exist_ok=True)

    # Save the figure
    plt.savefig(os.path.join(eval_folder, f'episode_{episode + 1}_eval.png'))
    plt.close()

def evaluate_performance(env, args, num_episodes=100, agent = None, train_name = 'czm', eval_folder="eval/eval_images", ):
    """
    Evaluates the performance of the agent in the WarehouseEnvironment.

    Args:
        env (WarehouseEnvironment): The environment instance.
        agent (Agent): The agent instance.
        num_episodes (int): The number of episodes to run for evaluation.
        eval_folder (str): The folder where evaluation images will be saved.

    Returns:
        dict: A dictionary containing the performance metrics.
    """

    device = torch.device("cuda" if torch.cuda.is_available() and args.cuda else "cpu")
    if agent == None:
        model = CNNLSTM().to(device)
        agent = PPOAgent(env, model, args, "eval_test")
    
    if args.eval:
        try:
            agent.load_model_only(f"{args.model_weigths}.pth")
            print(f"Loaded model weights from: {args.model_weigths}")
            time.sleep(2)
        except Exception as e:
            print(f"Error loading model weights: {e}")
            time.sleep(2)  
    else: 
        try:
            agent.load_model_only(f"eval/weights/{train_name}.pth")
            print(f"Loaded model weights from: eval/weights/{train_name}")
            time.sleep(2)
        except Exception as e:
            print(f"Error loading model weights: {e}")
            time.sleep(2)

    os.makedirs(eval_folder, exist_ok=True)

    total_moving_cost = 0
    total_detour_percentage = 0
    total_computing_time = 0
    failed_paths = 0
    total_reward = 0

    for episode in range(num_episodes):
        state, info = env.reset()
        start_cell = env.dynamic_coords[env.agent_idx][0]
        end_cell = env.dynamic_coords[env.agent_idx][-1]

        assert start_cell != end_cell, "Start and end cells are the same"
        print(f" ---------- Episode {episode + 1}/{num_episodes} ---------- ")
        
        value_map = map_to_value(env.init_arr.squeeze())
        optimal_path, _ = find_path(value_map, start_cell, end_cell)
      
        if optimal_path == 'fail':
            print("Optimal pathfinding failed before episode start.")
            optimal_path_coords = []
            optimal_path_length = 0
        else:
            optimal_path_coords = return_path(optimal_path)
            optimal_path_length = len(optimal_path_coords)
            print(f"Optimal path length: {optimal_path_length}")

        done = np.zeros(args.num_envs)
        steps = 0
        path = []
        episode_reward = 0
        start_time = time.time()

        # Initialize LSTM state
        lstm_state = agent.init_lstm_states(1)
        
        while not done:
            state_tensor = torch.FloatTensor(state).to(agent.device)
            with torch.no_grad():
                action, _, _, _, lstm_state = agent.model.get_action_and_value(
                    state_tensor, lstm_state, torch.zeros(1).to(agent.device), env, agent.device
                )
            
            action = action.cpu().numpy().item()
            next_state, reward, done, trunc, info = env.step(action)
            
            cell = env.agent_prev_coord
            state = next_state
            steps += 1
            episode_reward += reward

            cell = env.agent_prev_coord
            path.append(cell)

            if done or trunc:
                print("\nInfo:")
                for key, value in info.items():
                    print(f"  {key}: {value}")

        end_time = time.time()
        computing_time = (end_time - start_time) / steps

        manhattan_distance = abs(cell[0] - start_cell[0]) + abs(cell[1] - start_cell[1])
        moving_cost = steps / (manhattan_distance + 1e-7) if manhattan_distance != 0 else 0

        if optimal_path_length > 0:
            detour_percentage = ((steps - optimal_path_length) / optimal_path_length * 100)
        else:
            detour_percentage = 0
            failed_paths += 1

        total_moving_cost += moving_cost
        total_detour_percentage += detour_percentage
        total_computing_time += computing_time
        total_reward += episode_reward

        print(f"Episode {episode + 1} completed:")
        print(f"  Steps taken: {steps}")
        print(f"  Optimal path length: {optimal_path_length}")
        print(f"  Moving cost: {moving_cost:.4f}")
        print(f"  Detour percentage: {detour_percentage:.2f}%")
        print(f"  Computing time: {computing_time:.4f} s/step")
        print(f"  Episode reward: {episode_reward:.2f}")
        print(f"  Failed paths so far: {failed_paths}")
        print(f"  Reached goals for start-goal pair: {env.arrived}")
        print(f"  Reached goals so far: {env.terminations[0]}")
        print(f"  Terminations caused by reaching max steps: {env.terminations[2]}")
        print(f"  Terminations caused by having no global guidance: {env.terminations[1]}")
        print(f"  Terminations caused by collision with dynamic obstacles: {env.terminations[3]}")
        print(f" ---------------------------------------\n")

        # Save the evaluation image
        save_evaluation_image(env.init_arr, start_cell, end_cell, path, optimal_path_coords, episode, eval_folder)

    avg_reward = total_reward / num_episodes
    avg_moving_cost = total_moving_cost / num_episodes
    avg_detour_percentage = total_detour_percentage / num_episodes
    avg_computing_time = total_computing_time / num_episodes

    print("\n ---------- Evaluation Results: ----------")
    print(f"Average Reward: {avg_reward:.2f}")
    print(f"Average Moving Cost: {avg_moving_cost:.4f}")
    print(f"Average Detour Percentage: {avg_detour_percentage:.2f}%")
    print(f"Average Computing Time: {avg_computing_time:.4f} s/step")
    print(f"Total Failed Paths: {failed_paths}")
    print(f"Total Goals Reached: {env.terminations[0]:.0f}")
    print(f"Terminations caused by reaching max steps so far: {env.terminations[2]:.0f}")
    print(f"Terminations caused by having no global guidance so far: {env.terminations[1]:.0f}")
    print(f"Terminations caused by collision with dynamic obstacles so far: {env.terminations[3]:.0f}")
    print(f" ---------------------------------------- ")

    return {
        "avg_reward": avg_reward,
        "moving_cost": avg_moving_cost,
        "detour_percentage": avg_detour_percentage,
        "computing_time": avg_computing_time,
        "failed_paths": failed_paths,
        "agent_reached_goal": env.terminations[0],
        "max_steps_reached": env.terminations[2],
        "no_global_guidance": env.terminations[1],
        "collisions_with_obstacles": env.terminations[3]
    }