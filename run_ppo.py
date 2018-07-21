import os
import argparse
import gym
import numpy as np
import tensorflow as tf
from tqdm import tqdm

from network_models.policy_net import Policy_net
from algo.ppo import PPOTrain


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', help='log directory', default='log/train/ppo')
    parser.add_argument('--savedir', help='save directory', default='trained_models/ppo')
    parser.add_argument('--gamma', default=0.95, type=float)
    parser.add_argument('--iteration', default=int(1e4), type=int)
    parser.add_argument('--gpu_num', help='specify GPU number', default='0', type=str)
    return parser.parse_args()


def main(args):
    # $BJ]B8MQ%G%#%l%/%H%j$N=`Hw(B
    if not os.path.exists(args.logdir):
        os.makedirs(args.logdir)
    if not os.path.exists(args.savedir):
        os.makedirs(args.savedir)
    # $B4D6-$N%$%s%9%?%s%9(B
    env = gym.make('CartPole-v0')
    env.seed(0)
    ob_space = env.observation_space
    # $BJ}:v$N99?7A0$H99?78e$N(Bpolicy network$B$N=`Hw(B
    Policy = Policy_net('policy', env)
    Old_Policy = Policy_net('old_policy', env)
    PPO = PPOTrain(Policy, Old_Policy, gamma=args.gamma)
    # $B3X=,%m%0$NJ]B8(B
    saver = tf.train.Saver()
    # sessoin$B$N@_Dj(B
    config = tf.ConfigProto(
            gpu_options=tf.GPUOptions(
                visible_device_list=args.gpu_num,
                allow_growth=True
                ))

    # session
    with tf.Session(config=config) as sess:
        # summary$B$N=`Hw(B
        writer = tf.summary.FileWriter(args.logdir, sess.graph)
        # Sessionn$BFb$NJQ?t$N=i4|2=(B
        sess.run(tf.global_variables_initializer())
        # $B4D6-$N=i4|2=(B
        obs = env.reset()
        reward = 0
        success_num = 0

        # $B%$%F%l!<%7%g%s3+;O(B
        for iteration in tqdm(range(args.iteration)):
            observations = []
            actions = []
            v_preds = []
            rewards = []
            episode_length = 0
            # $B%(%T%=!<%I%k!<%W(B
            while True:
                episode_length += 1
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
                v_preds.append(v_pred)
                rewards.append(reward)

                # $BJ}:v$K$h$j7hDj$7$?9TF0$G4D6-$r99?7(B
                next_obs, reward, done, info = env.step(act)

                if done:
                    # next state of terminate state has 0 state value
                    # $B%(%T%=!<%I=*N;;~$N>uBV$N<!$N>uBV$N(Bvalue$B$r(B0$B$K$9$k(B
                    v_preds_next = v_preds[1:] + [0]
                    obs = env.reset()
                    reward = -1
                    break
                else:
                    obs = next_obs

            # episode$B$N(Blog
            writer.add_summary(
                    tf.Summary(
                        value=[tf.Summary.Value(
                            tag='episode_length',
                            simple_value=episode_length)]),
                    iteration)
            # rewards$B$N(Blog
            writer.add_summary(
                    tf.Summary(
                        value=[tf.Summary.Value(
                            tag='episode_reward',
                            simple_value=sum(rewards))]),
                    iteration)

            # $B<}1W$,(B195$B$r1[$($l$P=*N;$9$k(B
            if sum(rewards) >= 195:
                success_num += 1
                if success_num >= 100:
                    saver.save(sess, args.savedir+'/model.ckpt')
                    print('Clear!! Model saved.')
                    break
            else:
                success_num = 0

            gaes = PPO.get_gaes(rewards=rewards, v_preds=v_preds, v_preds_next=v_preds_next)

            # convert list to numpy array for feeding tf.placeholder
            observations = np.reshape(observations, newshape=[-1] + list(ob_space.shape))
            actions = np.array(actions).astype(dtype=np.int32)
            gaes = np.array(gaes).astype(dtype=np.float32)
            gaes = (gaes - gaes.mean()) / gaes.std()
            rewards = np.array(rewards).astype(dtype=np.float32)
            v_preds_next = np.array(v_preds_next).astype(dtype=np.float32)

            PPO.assign_policy_parameters()

            inp = [observations, actions, gaes, rewards, v_preds_next]

            # train
            for epoch in range(6):
                # sample indices from [low, high)
                sample_indices = np.random.randint(low=0, high=observations.shape[0], size=32)
                # sample training data
                sampled_inp = [np.take(a=a, indices=sample_indices, axis=0) for a in inp]
                PPO.train(
                        obs=sampled_inp[0],
                        actions=sampled_inp[1],
                        gaes=sampled_inp[2],
                        rewards=sampled_inp[3],
                        v_preds_next=sampled_inp[4])

            # PPO$B$N(Bsummary$B$N<hF@(B
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
