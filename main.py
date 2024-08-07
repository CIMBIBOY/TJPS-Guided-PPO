import argparse
from WarehouseEnv import WarehouseEnvironment
from train_utils import set_seed, print_cuda_info
from dqn_network import dqn_training
from q_learning import q_learning_training
from ppo_network import ppo_training
from parser_init import init_parser

'''
python3 main.py --render video --method mppo --epochs 100000 --timesteps 1000 --metal cpu --train scratch --batch 64 --train_name czm_ppo --cmd_log 5

python3 main.py --render off --method dqn --epochs 100000 --timesteps 33 --metal cuda --train retrain --model_weights weights/dqn_model_cuda_czm_1.pth --batch 32 --train_name czm_1 --cmd_log 5

python3 main.py --render off --method dqn --epochs 100000 --timesteps 33 --metal cuda --train scratch --batch 32 --train_name czm_1 --cmd_log 5
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parser for training script of G2RL.')
    init_parser(parser)
    args = parser.parse_args()

    # Set the seed for reproducibility
    set_seed(args.seed)

    num_ep = args.epochs
    num_timesteps = args.timesteps
    batch = args.batch
    train_name = args.train_name
    cmd_log = args.cmd_log
    exp = args.explore

    if args.render == 'video': video = True
    else: video = False

    if args.render == 'pygame':
        env = WarehouseEnvironment(pygame_render=True)
    elif args.render == 'off':
        env = WarehouseEnvironment(pygame_render=False)
    else:
        print("Render automatically set to False!")
        env = WarehouseEnvironment(pygame_render=False)

    if args.metal == 'cuda':
        metal = 'cuda'
        print_cuda_info()  # Print CUDA info if CUDA is selected
    elif args.metal == 'cpu':
        metal = 'cpu'
        print('Metal is CPU')
    else: print('Only cpu or cuda accelaration is supported')

    model_weights_path = None
    if args.train == 'retrain':
        if args.model_weights is None:
            parser.error("The --model_weights argument is required when --train is set to 'retrain'.")
        model_weights_path = args.model_weights

    if args.method == 'dqn':
        dqn_training(env, num_episodes = num_ep, timesteps_per_episode=num_timesteps, save_images = video, metal=metal, model_weights_path=model_weights_path, batch_size=batch, train_name=train_name, cmd_log=cmd_log, explore=exp)
    elif args.method == 'qnet':
        q_learning_training(env, num_episodes = num_ep, timesteps_per_episode=num_timesteps, save_images = video)   
    elif args.method == 'mppo': 
        ppo_training(env, num_episodes = num_ep, timesteps_per_episode=num_timesteps, save_images = video, device=metal, model_weights_path=model_weights_path, batch_size=batch, train_name=train_name, cmd_log=cmd_log)
    else: print("No method choosen or type error in parsing argument! Please eaither use command: \npython main.py --method dqn \nor\n python main.py --method qnet")

    env.close()

    