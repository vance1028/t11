import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu, theme, Button, Dropdown, Avatar, Space, Typography } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  TruckOutlined,
  ExperimentOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useEffect, useState } from 'react';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Requests from './pages/Requests';
import Dispatches from './pages/Dispatches';
import Compatibility from './pages/Compatibility';
import Login from './pages/Login';
import { authApi, UserInfo } from './api';

const { Header, Content, Sider } = Layout;
const { Text } = Typography;

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: <Link to="/">库存总览看板</Link>,
  },
  {
    key: '/inventory',
    icon: <DatabaseOutlined />,
    label: <Link to="/inventory">库存管理</Link>,
  },
  {
    key: '/requests',
    icon: <FileTextOutlined />,
    label: <Link to="/requests">用血申请</Link>,
  },
  {
    key: '/dispatches',
    icon: <TruckOutlined />,
    label: <Link to="/dispatches">调拨管理</Link>,
  },
  {
    key: '/compatibility',
    icon: <ExperimentOutlined />,
    label: <Link to="/compatibility">相容矩阵</Link>,
  },
];

const roleLabels: Record<string, string> = {
  ADMIN: '管理员',
  DOCTOR: '医生',
  NURSE: '护士',
  DISPATCHER: '调度员',
};

function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      const loggedIn = authApi.isAuthenticated();
      setIsLoggedIn(loggedIn);
      if (loggedIn) {
        setUser(authApi.getUser());
      } else if (location.pathname !== '/login') {
        navigate('/login');
      }
    };
    checkAuth();
  }, [location.pathname, navigate]);

  const handleLogout = () => {
    authApi.logout();
    setIsLoggedIn(false);
    setUser(null);
    navigate('/login');
  };

  const userMenu = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        onClick: handleLogout,
      },
    ],
  };

  if (location.pathname === '/login') {
    return <Login />;
  }

  if (!isLoggedIn) {
    return <Login />;
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#001529',
          padding: '0 24px',
        }}
      >
        <div
          style={{
            color: 'white',
            fontSize: '20px',
            fontWeight: 'bold',
          }}
        >
          🏥 区域血液调度协同系统
        </div>

        <div style={{ display: 'flex', alignItems: 'center' }}>
          {user && (
            <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer', color: 'white' }}>
              <Avatar icon={<UserOutlined />} />
              <div>
                <div style={{ fontSize: 14 }}>{user.real_name}</div>
                <div style={{ fontSize: 12, opacity: 0.8 }}>
                  {roleLabels[user.role] || user.role}
                </div>
              </div>
            </Space>
          </Dropdown>
        )}
        </div>
      </Header>
      <Layout>
        <Sider width={220} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/inventory" element={<Inventory />} />
              <Route path="/requests" element={<Requests />} />
              <Route path="/dispatches" element={<Dispatches />} />
              <Route path="/compatibility" element={<Compatibility />} />
              <Route path="/login" element={<Login />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
