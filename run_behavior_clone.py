import argparse
import gym
import numpy as np
import tensorflow as tf
from tqdm import tqdm

from network_models.policy_net import Policy_net
from algo.behavior_clone import BehavioralCloning


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--savedir', help='$B3X=,:Q$_%b%G%k$rJ]B8$9$k%G%#%l%/%H%j(B', default='trained_models/bc')
    parser.add_argument('--max_to_keep', help='$BJ]B8$9$k3X=,:Q$_%b%G%k$N8D?t(B', default=10, type=int)
    parser.add_argument('--logdir', help='log$B$N%G%#%l%/%H%j(B', default='log/train/bc')
    parser.add_argument('--iteration', default=int(1e3), type=int)
    parser.add_argument('--interval', help='$BJ]B8$N4V3V(B', default=int(1e2), type=int)
    parser.add_argument('--minibatch_size', help='$B%P%C%A%5%$%:(B', default=128, type=int)
    parser.add_argument('--epoch_num', help='$B%(%]%C%/?t(B', default=10, type=int)
    parser.add_argument('--gpu_num', help='specify GPU number', default='0', type=str)
    return parser.parse_args()


def main(args):
    env = gym.make('CartPole-v0')
    Policy = Policy_net('policy', env)
    BC = BehavioralCloning(Policy)
    saver = tf.train.Saver(max_to_keep=args.max_to_keep)

    # $B%(%-%9%Q!<%H$N(Btrajectories
    observations = np.genfromtxt('trajectory/observations.csv')
    actions = np.genfromtxt('trajectory/actions.csv', dtype=np.int32)
    # sessoin$B$N@_Dj(B
    config = tf.ConfigProto(
            gpu_options=tf.GPUOptions(
                visible_device_list=args.gpu_num,
                allow_growth=True
                ))

    # session
    with tf.Session(config=config) as sess:
        # log$B$N=`Hw(B
        writer = tf.summary.FileWriter(args.logdir, sess.graph)
        # $BJQ?t$N=i4|2=(B
        sess.run(tf.global_variables_initializer())

        # $B3X=,%G!<%?(B
        inp = [observations, actions]
        # $B%$%F%l!<%7%g%s3+;O(B
        for iteration in tqdm(range(args.iteration)):
            for epoch in range(args.epoch_num):
                # $B%5%s%W%j%s%0$9$k3X=,%G!<%?$N%$%s%G%C%/%9$r%i%s%@%`$KA*Br(B
                sample_indices = np.random.randint(low=0, high=observations.shape[0], size=args.minibatch_size)
                # $B3X=,%G!<%?$N%5%s%W%j%s%0(B
                sampled_inp = [np.take(a=a, indices=sample_indices, axis=0) for a in inp]
                # $B3X=,$N<B9T(B
                BC.train(obs=sampled_inp[0], actions=sampled_inp[1])

            # summary$B$N<hF@(B
            summary = BC.get_summary(obs=inp[0], actions=inp[1])

            if (iteration+1) % args.interval == 0:
                saver.save(sess, args.savedir + '/model.ckpt', global_step=iteration+1)
            # summary$B$N=q$-9~$_(B
            writer.add_summary(summary, iteration)
        writer.close()


if __name__ == '__main__':
    args = argparser()
    main(args)
