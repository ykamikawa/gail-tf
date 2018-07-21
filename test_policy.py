import gym
import numpy as np
import tensorflow as tf
import argparse
from network_models.policy_net import Policy_net


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--modeldir', help='$B3X=,:Q$_%b%G%k$N%G%#%l%/%H%j(B', default='trained_models')
    parser.add_argument('--alg', help='$B2=3X=,%"%k%4%j%:%`$r(Bgail, ppo, bc$B$+$iA*Br(B', default='gail')
    parser.add_argument('--model', help='test$B$KMQ$$$k3X=,:Q$_%b%G%k$NHV9f(B', default='')
    parser.add_argument('--logdir', help='log$B$N%G%#%l%/%H%j(B', default='log/test')
    parser.add_argument('--iteration', help='iterarion$B?t(B', default=int(1e3))
    parser.add_argument('--stochastic', help='$B3NN(E*$KJ}:v$rA*Br$9$k$+$I$&$+(B', action='store_false')
    return parser.parse_args()


def main(args):
    # gym$B4D6-$N:n@.(B
    env = gym.make('CartPole-v0')
    env.seed(0)
    Policy = Policy_net('policy', env)
    saver = tf.train.Saver()

    # session$B$N:n@.(B
    with tf.Session() as sess:
        # summary
        writer = tf.summary.FileWriter(args.logdir+'/'+args.alg, sess.graph)
        # $B%;%C%7%g%s$N=i4|2=(B
        sess.run(tf.global_variables_initializer())
        # $B3X=,:Q$_%b%G%k$NFI$_9~$_(B
        if args.model == '':
            saver.restore(sess, args.modeldir+'/'+args.alg+'/'+'model.ckpt')
        else:
            saver.restore(sess, args.modeldir+'/'+args.alg+'/'+'model.ckpt-'+args.model)
        # $B4QB,$N=i4|2=(B
        obs = env.reset()
        reward = 0
        success_num = 0

        # $B%$%F%l!<%7%g%s3+;O(B
        for iteration in range(args.iteration):
            rewards = []
            run_policy_steps = 0
            # $B%(%T%=!<%I$ND9$5$h$j$bC;$$(Bstep$B$GJ}:v$r<B9T(B
            while True:
                run_policy_steps += 1
                # prepare to feed placeholder Policy.obs
                # $B4QB,(B($B>uBV(B)$B$r%W%l!<%9%[%k%@!<MQ$KJQ49(B
                obs = np.stack([obs]).astype(dtype=np.float32)
                # $BJ}:v$r<B9T(B
                act, _ = Policy.act(obs=obs, stochastic=args.stochastic)

                # $BMWAG?t$,(B1$B$NG[Ns$r%9%+%i!<$KJQ49(B
                act = np.asscalar(act)
                # $B8=:_$NJs=7$rDI2C(B
                rewards.append(reward)

                # $BJ}:v$K$h$j7hDj$7$?9TF0$K$h$k4D6-$NJQ2=$r<hF@(B
                next_obs, reward, done, info = env.step(act)

                # $B%(%T%=!<%I$,=*N;$9$l$P4D6-$H(Breward$B$r%j%;%C%H(B
                if done:
                    obs = env.reset()
                    reward = -1
                    break
                else:
                    obs = next_obs

            # summary$B$N=q$-9~$_(B
            writer.add_summary(
                    tf.Summary(value=[tf.Summary.Value(tag='episode_length', simple_value=run_policy_steps)]),
                    iteration)
            writer.add_summary(
                    tf.Summary(value=[tf.Summary.Value(tag='episode_reward', simple_value=sum(rewards))]),
                    iteration)

            # 100$B2s0J>e%/%j%"$G$-$l$P(Biterarion$B$r=*N;(B
            if sum(rewards) >= 195:
                success_num += 1
                if success_num >= 100:
                    print('Iteration: ', iteration)
                    print('Clear!!')
                    break
            else:
                success_num = 0

        writer.close()


if __name__ == '__main__':
    args = argparser()
    main(args)
