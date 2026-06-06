import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, theme } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  TruckOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Requests from './pages/Requests';
import Dispatches from './pages/Dispatches';
import Compatibility from './pages/Compatibility';

const { Header, Content, Sider } = Layout;

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

function App() {
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#001529',
          padding: '0 24px',
        }}
      >
        <div
          style={{
            color: 'white',
            fontSize: '20px',
            fontWeight: 'bold',
            marginRight: '48px',
          }}
        >
          🏥 区域血液调度协同系统
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
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
