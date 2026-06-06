import { useEffect, useState } from 'react';
import {
  Table,
  Tag,
  Space,
  Button,
  Select,
  Row,
  Col,
  Typography,
  Modal,
  Form,
  Input,
  DatePicker,
  InputNumber,
  message,
  Popconfirm,
} from 'antd';
import {
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { inventoryApi } from '../api';
import type { BloodBag } from '../types';
import {
  BloodType,
  RhType,
  BloodComponent,
  BagStatus,
} from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;

const componentLabels: Record<BloodComponent, string> = {
  [BloodComponent.RBC]: '红细胞',
  [BloodComponent.PLASMA]: '血浆',
  [BloodComponent.PLATELET]: '血小板',
  [BloodComponent.CRYOPRECIPITATE]: '冷沉淀',
};

const statusColors: Record<BagStatus, string> = {
  [BagStatus.PENDING_TEST]: 'default',
  [BagStatus.IN_STOCK]: 'green',
  [BagStatus.DISPATCHED]: 'blue',
  [BagStatus.SCRAPPED]: 'red',
};

const statusLabels: Record<BagStatus, string> = {
  [BagStatus.PENDING_TEST]: '待检',
  [BagStatus.IN_STOCK]: '在库',
  [BagStatus.DISPATCHED]: '已出库',
  [BagStatus.SCRAPPED]: '已报废',
};

function Inventory() {
  const [bags, setBags] = useState<BloodBag[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    blood_type: undefined as BloodType | undefined,
    rh_type: undefined as RhType | undefined,
    component: undefined as BloodComponent | undefined,
    only_in_stock: true,
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadBags();
  }, [filters]);

  const loadBags = async () => {
    setLoading(true);
    try {
      const res = await inventoryApi.getAll(filters);
      setBags(res.data);
    } catch (error) {
      message.error('加载库存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleScrap = async (id: string, reason: string) => {
    try {
      await inventoryApi.scrap(id, reason);
      message.success('已报废');
      loadBags();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '报废失败');
    }
  };

  const handleCreate = async (values: any) => {
    try {
      const data = {
        ...values,
        collection_date: values.collection_date.format('YYYY-MM-DD'),
        expiry_date: values.expiry_date.format('YYYY-MM-DD'),
      };
      await inventoryApi.create(data);
      message.success('添加成功');
      setModalVisible(false);
      form.resetFields();
      loadBags();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '添加失败');
    }
  };

  const columns = [
    {
      title: '血袋编号',
      dataIndex: 'bag_number',
      key: 'bag_number',
      width: 140,
    },
    {
      title: '血型',
      key: 'bloodType',
      width: 80,
      render: (_: any, r: BloodBag) =>
        `${r.blood_type}${r.rh_type === 'POSITIVE' ? '+' : '-'}`,
    },
    {
      title: '成分',
      dataIndex: 'component',
      key: 'component',
      width: 90,
      render: (c: BloodComponent) => componentLabels[c],
    },
    {
      title: '采血日期',
      dataIndex: 'collection_date',
      key: 'collection_date',
      width: 110,
      render: (d: string) => dayjs(d).format('YYYY-MM-DD'),
    },
    {
      title: '有效期至',
      dataIndex: 'expiry_date',
      key: 'expiry_date',
      width: 110,
      render: (d: string, r: BloodBag) => {
        const days = r.days_to_expiry ?? 0;
        let color = 'inherit';
        if (days <= 0) color = '#ff4d4f';
        else if (days <= 3) color = '#fa8c16';
        else if (days <= 7) color = '#faad14';

        return (
          <span style={{ color }}>
            {dayjs(d).format('YYYY-MM-DD')}
            {days <= 0 && ' (已过期)'}
            {days > 0 && days <= 7 && ` (剩${days}天)`}
          </span>
        );
      },
      sorter: (a: BloodBag, b: BloodBag) =>
        dayjs(a.expiry_date).valueOf() - dayjs(b.expiry_date).valueOf(),
    },
    {
      title: '容量',
      dataIndex: 'volume_ml',
      key: 'volume',
      width: 80,
      render: (v: number) => `${v}ml`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (s: BagStatus) => (
        <Tag color={statusColors[s]}>{statusLabels[s]}</Tag>
      ),
    },
    {
      title: '库位',
      dataIndex: 'location',
      key: 'location',
      width: 120,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: any, r: BloodBag) =>
        r.status === BagStatus.IN_STOCK ? (
          <Popconfirm
            title="确认报废此血袋？"
            description="请输入报废原因"
            onConfirm={() => handleScrap(r.id, '人工报废')}
            okText="确认"
            cancelText="取消"
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              报废
            </Button>
          </Popconfirm>
        ) : null,
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginTop: 0 }}>
        库存管理
      </Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Select
            placeholder="血型"
            style={{ width: 100 }}
            allowClear
            value={filters.blood_type}
            onChange={(v) => setFilters({ ...filters, blood_type: v })}
          >
            {Object.values(BloodType).map((bt) => (
              <Option key={bt} value={bt}>
                {bt}
              </Option>
            ))}
          </Select>
        </Col>
        <Col>
          <Select
            placeholder="Rh"
            style={{ width: 100 }}
            allowClear
            value={filters.rh_type}
            onChange={(v) => setFilters({ ...filters, rh_type: v })}
          >
            <Option value={RhType.POSITIVE}>Rh+</Option>
            <Option value={RhType.NEGATIVE}>Rh-</Option>
          </Select>
        </Col>
        <Col>
          <Select
            placeholder="成分"
            style={{ width: 120 }}
            allowClear
            value={filters.component}
            onChange={(v) => setFilters({ ...filters, component: v })}
          >
            {Object.entries(componentLabels).map(([key, label]) => (
              <Option key={key} value={key}>
                {label}
              </Option>
            ))}
          </Select>
        </Col>
        <Col>
          <Select
            style={{ width: 120 }}
            value={filters.only_in_stock ? 'in_stock' : 'all'}
            onChange={(v) =>
              setFilters({ ...filters, only_in_stock: v === 'in_stock' })
            }
          >
            <Option value="in_stock">仅在库</Option>
            <Option value="all">全部</Option>
          </Select>
        </Col>
        <Col style={{ marginLeft: 'auto' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            登记血袋
          </Button>
        </Col>
      </Row>

      <Table
        columns={columns}
        dataSource={bags}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1000 }}
      />

      <Modal
        title="登记血袋"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="血袋编号"
                name="bag_number"
                rules={[{ required: true }]}
              >
                <Input placeholder="唯一编号" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="血型"
                name="blood_type"
                rules={[{ required: true }]}
              >
                <Select>
                  {Object.values(BloodType).map((bt) => (
                    <Option key={bt} value={bt}>
                      {bt}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="Rh"
                name="rh_type"
                rules={[{ required: true }]}
              >
                <Select>
                  <Option value={RhType.POSITIVE}>Rh+</Option>
                  <Option value={RhType.NEGATIVE}>Rh-</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="成分"
                name="component"
                rules={[{ required: true }]}
              >
                <Select>
                  {Object.entries(componentLabels).map(([key, label]) => (
                    <Option key={key} value={key}>
                      {label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="容量(ml)"
                name="volume_ml"
                initialValue={200}
              >
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="采血日期"
                name="collection_date"
                rules={[{ required: true }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="有效期至"
                name="expiry_date"
                rules={[{ required: true }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="库位" name="location">
            <Input placeholder="冷库位置" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default Inventory;
