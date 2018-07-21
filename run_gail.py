import argparse
import gym
import numpy as np
import tensorflow as tf
from tqdm import tqdm

from network_models.policy_net import Policy_net
from network_models.discriminator import Discriminator
from algo.ppo import PPOTrain


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', help='log directory', default='log/train/gail')
    parser.add_argument('--savedir', help='save directory', default='trained_models/gail')
    parser.add_argument('--gamma', default=0.95)
    parser.add_argument('--iteration', default=int(1e4))
    parser.add_argument('--gpu_num', help='specify GPU number', default='0', type=str)
    return parser.parse_args()


def main(args):
    # $B4D6-$N:n@.(B
    env = gym.make('CartPole-v0')
    env.seed(0)
    ob_space = env.observation_space
    # $BF~NO(B: $B4QB,(B, $B=PNO(B: $B9TF0$NJ,I[$H<}1W$N4|BTCM$N(BPolicy_net
    Policy = Policy_net('policy', env)
    Old_Policy = Policy_net('old_policy', env)
    # PPO$B3X=,MQ$N%$%s%9%?%s%9(B
    PPO = PPOTrain(Policy, Old_Policy, gamma=args.gamma)
    # discriminator
    D = Discriminator(env)

    # $B%(%-%9%Q!<%H$N(Btrajectories
    expert_observations = np.genfromtxt('trajectory/observations.csv')
    expert_actions = np.genfromtxt('trajectory/actions.csv', dtype=np.int32)

    # $B3X=,:Q$_%b%G%kJ]B8MQ(B
    saver = tf.train.Saver()
    # sessoin$B$N@_Dj(B
    config = tf.ConfigProto(
            gpu_options=tf.GPUOptions(
                visible_device_list=args.gpu_num,
                allow_growth=True
                ))

    with tf.Session(config=config) as sess:
        # summary$B$N=`Hw(B
        writer = tf.summary.FileWriter(args.logdir, sess.graph)
        # session$BFb$NJQ?t$N=i4|2=(B
        sess.run(tf.global_variables_initializer())
        # $B4D6-$N=i4|2=(B
        obs = env.reset()
        reward = 0
        success_num = 0

        for iteration in tqdm(range(args.iteration)):
            observations = []
            actions = []
            rewards = []
            v_preds = []
            run_policy_steps = 0
            # $B%(%T%=!<%I%k!<%W(B
            while True:
                run_policy_steps += 1
                # $B4QB,$r%W%l!<%9%[%k%@!<MQ$KJQ49(B
                obs = np.stack([obs]).astype(dtype=np.float32)
                # policy net$B$K4QB,$rF~NO$7(B,$B9TF0$H?dDj<}1W$r<hF@(B
                act, v_pred = Policy.act(obs=obs, stochastic=True)

                # $BMWAG?t$,(B1$B$NG[Ns$r%9%+%i!<$KJQ49(B
                act = np.asscalar(act)
                v_pred = np.asscalar(v_pred)

                # $B8=:_$N>uBV$rDI2C(B
                observations.append(obs)
                actions.append(act)
                rewards.append(reward)
                v_preds.append(v_pred)

                # $BJ}:v$K$h$j7hDj$7$?9TF0$G4D6-$r99?7(B
                next_obs, reward, done, info = env.step(act)

                # $B%(%T%=!<%I$,=*N;$9$l$P4D6-$H(Breward$B$r%j%;%C%H(B
                if done:
                    v_preds_next = v_preds[1:] + [0]
                    obs = env.reset()
                    reward = -1
                    break
                else:
                    obs = next_obs

            # summary$B$N=q$-9~$_(B
            writer.add_summary(
                    tf.Summary(value=[tf.Summary.Value(
                        tag='episode_length',
                        simple_value=run_policy_steps)]),
                    iteration)
            writer.add_summary(
                    tf.Summary(value=[tf.Summary.Value(
                        tag='episode_reward',
                        simple_value=sum(rewards))]),
                    iteration)

            # 100$B2s0J>e%/%j%"$G$-$l$P(Biterarion$B$r=*N;(B
            if sum(rewards) >= 195:
                success_num += 1
                if success_num >= 100:
                    saver.save(sess, args.savedir + '/model.ckpt')
                    print('Clear!! Model saved.')
                    break
            else:
                success_num = 0

            # Discriminator$B$N3X=,(B
            # $B4QB,$H9TF0$r%W%l!<%9%[%k%@!<MQ$KJQ49(B
            observations = np.reshape(observations, newshape=[-1] + list(ob_space.shape))
            actions = np.array(actions).astype(dtype=np.int32)

            # Discriminator$B$N3X=,%k!<%W(B
            for i in range(2):
                D.train(expert_s=expert_observations,
                        expert_a=expert_actions,
                        agent_s=observations,
                        agent_a=actions)

            # Discriminator$B$N=PNO$rJs=7$H$7$FMxMQ(B
            d_rewards = D.get_rewards(agent_s=observations, agent_a=actions)
            d_rewards = np.reshape(d_rewards, newshape=[-1]).astype(dtype=np.float32)

            # d_rewards$B$rMQ$$$F(Bgaes$B$r<hF@(B
            gaes = PPO.get_gaes(rewards=d_rewards, v_preds=v_preds, v_preds_next=v_preds_next)
            gaes = np.array(gaes).astype(dtype=np.float32)
            # gaes = (gaes - gaes.mean()) / gaes.std()
            v_preds_next = np.array(v_preds_next).astype(dtype=np.float32)

            # d_rewards$B$rMQ$$$F(BPolicy_net$B$N3X=,(B
            inp = [observations, actions, gaes, d_rewards, v_preds_next]
            # Old_Policy$B$K(BPolicy_net$B$N%Q%i%a!<%?$rBeF~(B
            PPO.assign_policy_parameters()

            # PPO$B$N3X=,(B
            for epoch in range(6):
                # indices are in [low, high)
                sample_indices = np.random.randint(
                        low=0,
                        high=observations.shape[0],
                        size=32)
                # $B3X=,%G!<%?$r%5%s%W%k(B
                sampled_inp = [np.take(a=a, indices=sample_indices, axis=0) for a in inp]
                PPO.train(
                        obs=sampled_inp[0],
                        actions=sampled_inp[1],
                        gaes=sampled_inp[2],
                        rewards=sampled_inp[3],
                        v_preds_next=sampled_inp[4])

            # summary$B$N<hF@(B
            summary = PPO.get_summary(
                    obs=inp[0],
                    actions=inp[1],
                    gaes=inp[2],
                    rewards=inp[3],
                    v_preds_next=inp[4])

            writer.add_summary(summary, iteration)
        writer.close()


if __name__ == '__main__':
    args = argparser()
    main(args)
