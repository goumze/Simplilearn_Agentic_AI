resource "aws_dynamodb_table" "travel_packages" {
  name         = var.table_name
  billing_mode = var.billing_mode
  hash_key     = var.partition_key

  attribute {
    name = var.partition_key
    type = "S"
  }

  tags = var.tags
}

# Seed item for Mumbai. Typed DynamoDB JSON: every attribute is {"S": "..."}.
resource "aws_dynamodb_table_item" "mumbai" {
  table_name = aws_dynamodb_table.travel_packages.name
  hash_key   = aws_dynamodb_table.travel_packages.hash_key

  item = jsonencode({
    city = { S = "Mumbai" }
    travel_plan = {
      S = "Day 1: Explore Gateway of India and Marine Drive waterfront. Day 2: Visit Elephanta Caves via ferry and Crawford Market for shopping. Day 3: Tour Bollywood studios and enjoy street food in Mohammed Ali Road. Day 4: Relax at Juhu Beach and visit Haji Ali Dargah. Day 5: Shopping at Linking Road and departure from Chhatrapati Shivaji Airport."
    }
    vacation_cost = { S = "$500-800" }
    duration      = { S = "5 days" }
  })
}
