import { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api';

const { Title } = Typography;

function Login() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const res = await authApi.login(values.username, values.password);
      authApi.setAuth(res.data);
      message.success(`欢迎回来，${res.data.real_name}`);
      navigate('/');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        style={{
          width: 400,
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>🏥</div>
          <Title level={3} style={{ marginBottom: 4 }}>
            区域血液调度协同系统
          </Title>
          <p style={{ color: '#999', margin: 0 }}>请登录以继续</p>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loading}
              size="large"
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div
          style={{
            marginTop: 24,
            paddingTop: 16,
            borderTop: '1px solid #f0f0f0',
            fontSize: 12,
            color: '#999',
          }}
        >
          <p style={{ marginBottom: 4 }}>测试账号：</p>
          <ul style={{ margin: 0, paddingLeft: 16 }}>
            <li>管理员：admin / admin123</li>
            <li>医生：doctor / doctor123</li>
            <li>护士：nurse / nurse123</li>
            <li>调度员：dispatcher / dispatcher123</li>
          </ul>
        </div>
      </Card>
    </div>
  );
}

export default Login;
