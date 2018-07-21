import tensorflow as tf


class Policy_net:
    def __init__(self, name: str, env):
        """
        name: $B%M%C%H%o!<%/$NL>A0(B
        env: gym$B$N4D6-(B
        """

        # $B>uBV=89g(B
        ob_space = env.observation_space
        # $B9TF0=89g(B
        act_space = env.action_space

        with tf.variable_scope(name):
            # $B4QB,$7$?(Btrajectories$B$N%W%l!<%9%[%k%@!<(B
            self.obs = tf.placeholder(dtype=tf.float32, shape=[None] + list(ob_space.shape), name='obs')

            # $BJ}:vMQ(B
            with tf.variable_scope('policy_net'):
                # $BF~NO(B: $B>uBV(B, $B=PNO(B: $B9TF0(B
                layer_1 = tf.layers.dense(inputs=self.obs, units=20, activation=tf.tanh)
                layer_2 = tf.layers.dense(inputs=layer_1, units=20, activation=tf.tanh)
                layer_3 = tf.layers.dense(inputs=layer_2, units=act_space.n, activation=tf.tanh)
                self.act_probs = tf.layers.dense(inputs=layer_3, units=act_space.n, activation=tf.nn.softmax)

            # $B<}1WMQ(B
            with tf.variable_scope('value_net'):
                # $BF~NO(B: $B>uBV(B, $B=PNO(B: $B<}1W(B
                layer_1 = tf.layers.dense(inputs=self.obs, units=20, activation=tf.tanh)
                layer_2 = tf.layers.dense(inputs=layer_1, units=20, activation=tf.tanh)
                self.v_preds = tf.layers.dense(inputs=layer_2, units=1, activation=None)

            # $B9TF0$NJ,I[$+$i3NN(E*$K9TF0$rA*Br(B
            self.act_stochastic = tf.multinomial(tf.log(self.act_probs), num_samples=1)
            self.act_stochastic = tf.reshape(self.act_stochastic, shape=[-1])

            # $B9TF0$NJ,I[$+$i7hDjE*$K9TF0$rA*Br$D$^$j:GBgCM$N%$%s%G%C%/%9(B
            self.act_deterministic = tf.argmax(self.act_probs, axis=1)

            self.scope = tf.get_variable_scope().name

    def act(self, obs, stochastic=True):
        '''
        obs: $B4QB,(B
        stochastic: $B3NN(E*$JJ}:v$rMQ$$$k$+$I$&$+(B
        return: $B9TF0$H<}1W$N4|BTCM(B
        '''
        if stochastic:
            return tf.get_default_session().run(
                    [self.act_stochastic, self.v_preds],
                    feed_dict={self.obs: obs})
        else:
            return tf.get_default_session().run(
                    [self.act_deterministic, self.v_preds],
                    feed_dict={self.obs: obs})

    def get_action_prob(self, obs):
        '''
        obs: $B4QB,(B
        return: $B9TF0$NJ,I[(B
        '''
        return tf.get_default_session().run(
                self.act_probs,
                feed_dict={self.obs: obs})

    def get_variables(self):
        '''$B%M%C%H%o!<%/$NA4%Q%i%a!<%?<hF@(B'''
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.scope)

    def get_trainable_variables(self):
        '''$B3X=,BP>]$N%M%C%H%o!<%/$N%Q%i%a!<%?<hF@(B'''
        return tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, self.scope)
